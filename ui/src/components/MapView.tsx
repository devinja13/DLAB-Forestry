import { useEffect, useRef, useState } from 'react';
import maplibregl, { LngLatLike } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { GeoJsonLayer } from '@deck.gl/layers';
import { HeatmapLayer } from '@deck.gl/aggregation-layers';

import CellTooltip from './CellTooltip';
import {
  Bbox,
  useOptimizeStore,
} from '../store/useOptimizeStore';
import { cellsToGeoJson } from '../utils/cellsToGeoJson';
import { colorByDominantType } from '../utils/colorByType';
import { regionsToGeoJson } from '../utils/regionsToGeoJson';

const HOUSTON_CENTER: [number, number] = [-95.3698, 29.7604];

function normalizeBbox(a: maplibregl.LngLat, b: maplibregl.LngLat): Bbox {
  return {
    west: Math.min(a.lng, b.lng),
    south: Math.min(a.lat, b.lat),
    east: Math.max(a.lng, b.lng),
    north: Math.max(a.lat, b.lat),
  };
}

function bboxToFeature(bbox: Bbox) {
  return {
    type: 'FeatureCollection' as const,
    features: [
      {
        type: 'Feature' as const,
        geometry: {
          type: 'Polygon' as const,
          coordinates: [
            [
              [bbox.west, bbox.south],
              [bbox.east, bbox.south],
              [bbox.east, bbox.north],
              [bbox.west, bbox.north],
              [bbox.west, bbox.south],
            ],
          ],
        },
        properties: {},
      },
    ],
  };
}

const MapView: React.FC = () => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const overlay = useRef<MapboxOverlay | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [draftStart, setDraftStart] = useState<maplibregl.LngLat | null>(null);
  const [draftCurrent, setDraftCurrent] = useState<maplibregl.LngLat | null>(null);

  const {
    result,
    visibleLayers,
    setHoveredCell,
    hoveredCell,
    jobStatus,
    regions,
    isDrawingRegion,
    addRegion,
  } = useOptimizeStore();

  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center: HOUSTON_CENTER as LngLatLike,
      zoom: 10,
    });

    map.current.addControl(new maplibregl.NavigationControl(), 'bottom-right');

    overlay.current = new MapboxOverlay({ layers: [] });
    map.current.addControl(overlay.current as unknown as maplibregl.IControl);
    map.current.on('load', () => setMapLoaded(true));

    return () => {
      overlay.current?.finalize();
      map.current?.remove();
      map.current = null;
    };
  }, []);

  useEffect(() => {
    if (!mapLoaded || !map.current) return;

    const handleClick = (event: maplibregl.MapMouseEvent) => {
      if (!isDrawingRegion) return;

      if (!draftStart) {
        setDraftStart(event.lngLat);
        setDraftCurrent(event.lngLat);
        return;
      }

      const bbox = normalizeBbox(draftStart, event.lngLat);
      addRegion(bbox);
      setDraftStart(null);
      setDraftCurrent(null);
    };

    const handleMove = (event: maplibregl.MapMouseEvent) => {
      if (isDrawingRegion && draftStart) {
        setDraftCurrent(event.lngLat);
      }
    };

    map.current.on('click', handleClick);
    map.current.on('mousemove', handleMove);

    return () => {
      map.current?.off('click', handleClick);
      map.current?.off('mousemove', handleMove);
    };
  }, [addRegion, draftStart, isDrawingRegion, mapLoaded]);

  useEffect(() => {
    if (!isDrawingRegion) {
      setDraftStart(null);
      setDraftCurrent(null);
    }
  }, [isDrawingRegion]);

  useEffect(() => {
    if (!mapLoaded || !overlay.current) return;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const layers: any[] = [];

    if (result && visibleLayers.has('cooling')) {
      const heatmapData = result.cells.map((cell) => ({
        coordinates: [cell.lng, cell.lat] as [number, number],
        weight: cell.cooling_delta,
      }));
      const maxCooling = Math.max(...result.cells.map((cell) => cell.cooling_delta), 0.001);

      layers.push(
        new HeatmapLayer({
          id: 'cooling-heatmap',
          data: heatmapData,
          getPosition: (d: { coordinates: [number, number] }) => d.coordinates,
          getWeight: (d: { weight: number }) => d.weight,
          colorDomain: [0, maxCooling] as [number, number],
          colorRange: [
            [236, 245, 251, 255],
            [144, 213, 235, 255],
            [29, 158, 117, 255],
            [186, 117, 23, 255],
            [216, 90, 48, 255],
          ] as [number, number, number, number][],
          radiusPixels: 40,
          intensity: 1.2,
          threshold: 0.03,
        }),
      );
    }

    if (result && visibleLayers.has('trees')) {
      layers.push(
        new GeoJsonLayer({
          id: 'tree-cells',
          data: cellsToGeoJson(result.cells),
          filled: true,
          stroked: true,
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          getFillColor: (feature: any) => colorByDominantType(feature.properties),
          getLineColor: [255, 255, 255, 120] as [number, number, number, number],
          lineWidthMinPixels: 0.5,
          pickable: true,
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          onHover: (info: any) => {
            setHoveredCell(info.object ? info.object.properties : null);
          },
        }),
      );
    }

    if (visibleLayers.has('regions') && regions.length > 0) {
      layers.push(
        new GeoJsonLayer({
          id: 'selected-regions',
          data: regionsToGeoJson(regions),
          filled: true,
          stroked: true,
          getFillColor: [245, 158, 11, 40],
          getLineColor: [217, 119, 6, 220],
          lineWidthMinPixels: 2,
        }),
      );
    }

    if (isDrawingRegion && draftStart && draftCurrent) {
      layers.push(
        new GeoJsonLayer({
          id: 'draft-region',
          data: bboxToFeature(normalizeBbox(draftStart, draftCurrent)),
          filled: true,
          stroked: true,
          getFillColor: [59, 130, 246, 35],
          getLineColor: [37, 99, 235, 230],
          lineWidthMinPixels: 2,
        }),
      );
    }

    overlay.current.setProps({ layers });
  }, [
    draftCurrent,
    draftStart,
    isDrawingRegion,
    mapLoaded,
    regions,
    result,
    setHoveredCell,
    visibleLayers,
  ]);

  return (
    <div className="absolute inset-0 w-full h-full">
      <div ref={mapContainer} className="absolute inset-0" />

      {isDrawingRegion && (
        <div className="absolute top-4 left-4 z-30 rounded-lg bg-white/95 px-4 py-3 shadow-lg">
          <p className="text-sm font-semibold text-slate-800">Draw a constrained region</p>
          <p className="text-xs text-slate-500">
            Click one corner, then click the opposite corner to create a region.
          </p>
        </div>
      )}

      {(jobStatus === 'pending' || jobStatus === 'running') && (
        <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm z-30 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg shadow-xl max-w-sm w-full text-center flex flex-col items-center">
            <div className="w-12 h-12 border-4 border-slate-200 border-t-green-600 rounded-full animate-spin mb-4" />
            <h3 className="text-lg font-bold text-slate-800 mb-1">Running optimization</h3>
            <p className="text-sm text-slate-500">
              Gurobi is solving the planting model with your selected tree catalog and regional
              constraints.
            </p>
          </div>
        </div>
      )}

      {hoveredCell && <CellTooltip cell={hoveredCell} />}
    </div>
  );
};

export default MapView;
