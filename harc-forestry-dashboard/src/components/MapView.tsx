import React, { useRef, useEffect, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useScenarioStore } from '../store/useScenarioStore';

const MapView: React.FC = () => {
    const mapContainer = useRef<HTMLDivElement>(null);
    const map = useRef<maplibregl.Map | null>(null);
    const [mapLoaded, setMapLoaded] = useState(false);

    const { trees, isOptimizing, timeHorizon } = useScenarioStore();

    // Initialize Map
    useEffect(() => {
        if (map.current || !mapContainer.current) return;

        map.current = new maplibregl.Map({
            container: mapContainer.current,
            style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
            center: [-95.3698, 29.7604],
            zoom: 11
        });

        map.current.addControl(new maplibregl.NavigationControl(), 'bottom-right');

        map.current.on('load', () => {
            setMapLoaded(true);
        });

        return () => {
            map.current?.remove();
            map.current = null;
            setMapLoaded(false);
        };
    }, []);

    // Render tree markers
    useEffect(() => {
        if (!map.current || !mapLoaded) return;

        const treeFeatures = trees.map(tree => {
            // Logic for size visualization based on time horizon
            const yearsGrown = Math.max(0, timeHorizon - tree.yearPlanted);
            const isVisible = tree.yearPlanted <= timeHorizon;

            let baseRadius = 5;
            if (tree.type === 'Medium') baseRadius = 8;
            if (tree.type === 'Large') baseRadius = 12;

            const currentRadius = isVisible ? baseRadius + (yearsGrown * 0.5) : 0;

            return {
                type: 'Feature',
                properties: {
                    id: tree.id,
                    type: tree.type,
                    radius: currentRadius,
                    visible: isVisible
                },
                geometry: { type: 'Point', coordinates: [tree.lng, tree.lat] }
            };
        }).filter(f => f.properties.visible);

        const data = {
            type: 'FeatureCollection',
            features: treeFeatures
        };

        const source = map.current.getSource('trees-source') as maplibregl.GeoJSONSource;

        if (source) {
            source.setData(data as any);
        } else if (map.current.isStyleLoaded()) {
            map.current.addSource('trees-source', {
                type: 'geojson',
                data: data as any
            });

            map.current.addLayer({
                id: 'trees-layer',
                type: 'circle',
                source: 'trees-source',
                paint: {
                    'circle-radius': ['get', 'radius'],
                    'circle-color': '#059669',
                    'circle-stroke-width': 2,
                    'circle-stroke-color': '#ffffff',
                    'circle-opacity': 0.9
                }
            });
        }
    }, [trees, timeHorizon, mapLoaded]);

    return (
        <div className="absolute inset-0 w-full h-full bg-slate-100 relative">
            <div ref={mapContainer} className="absolute inset-0" />

            {/* Optimization Status Overlay */}
            {isOptimizing && (
                <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm z-30 flex flex-col items-center justify-center transition-all duration-300">
                    <div className="bg-white p-6 rounded-lg shadow-xl max-w-sm w-full text-center border border-slate-100 flex flex-col items-center">
                        <div className="w-12 h-12 border-4 border-slate-200 border-t-planning-accent rounded-full animate-spin mb-4 shadow-sm" />
                        <h3 className="text-lg font-bold text-slate-800 mb-1">Computing Optimal Scenario</h3>
                        <p className="text-sm text-slate-500">
                            Simulating heat reduction and finding optimal placements based on your budget constraints...
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MapView;
