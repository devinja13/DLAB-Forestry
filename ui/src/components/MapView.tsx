import { useRef, useEffect, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { GeoJsonLayer } from '@deck.gl/layers';
import { HeatmapLayer } from '@deck.gl/aggregation-layers';
import { useOptimizeStore } from '../store/useOptimizeStore';
import { cellsToGeoJson } from '../utils/cellsToGeoJson';
import { colorByDominantType } from '../utils/colorByType';
import CellTooltip from './CellTooltip';

const HOUSTON_CENTER: [number, number] = [-95.3698, 29.7604];

const MapView: React.FC = () => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const overlay = useRef<MapboxOverlay | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  const { result, visibleLayers, setHoveredCell, hoveredCell, jobStatus } =
    useOptimizeStore();

  // --- Init map ---
  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center: HOUSTON_CENTER,
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

  // --- Update deck.gl layers when result or visibility changes ---
  useEffect(() => {
    if (!mapLoaded || !overlay.current) return;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const layers: any[] = [];

    if (result && visibleLayers.has('cooling')) {
      const heatmapData = result.cells.map((c) => ({
        coordinates: [c.lng, c.lat] as [number, number],
        weight: c.cooling_delta,
      }));

      const maxCooling = Math.max(...result.cells.map((c) => c.cooling_delta), 0.001);

      layers.push(
        new HeatmapLayer({
          id: 'cooling-heatmap',
          data: heatmapData,
          getPosition: (d: { coordinates: [number, number]; weight: number }) =>
            d.coordinates,
          getWeight: (d: { coordinates: [number, number]; weight: number }) =>
            d.weight,
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
      const geojson = cellsToGeoJson(result.cells);

      layers.push(
        new GeoJsonLayer({
          id: 'tree-cells',
          data: geojson,
          filled: true,
          stroked: true,
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          getFillColor: (f: any) => colorByDominantType(f.properties),
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

    overlay.current.setProps({ layers });
  }, [result, visibleLayers, mapLoaded, setHoveredCell]);

  return (
    <div className="absolute inset-0 w-full h-full">
      <div ref={mapContainer} className="absolute inset-0" />

      {/* Loading overlay while job runs */}
      {(jobStatus === 'pending' || jobStatus === 'running') && (
        <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm z-30 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg shadow-xl max-w-sm w-full text-center flex flex-col items-center">
            <div className="w-12 h-12 border-4 border-slate-200 border-t-green-600 rounded-full animate-spin mb-4" />
            <h3 className="text-lg font-bold text-slate-800 mb-1">Running optimization</h3>
            <p className="text-sm text-slate-500">
              Gurobi is solving the planting model. This may take up to 2 minutes for full
              Houston.
            </p>
          </div>
        </div>
      )}

      {/* Cell hover tooltip */}
      {hoveredCell && <CellTooltip cell={hoveredCell} />}
    </div>
  );
};

export default MapView;
