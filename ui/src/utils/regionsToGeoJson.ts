import { RegionConstraint } from '../store/useOptimizeStore';

export function regionsToGeoJson(regions: RegionConstraint[]) {
  return {
    type: 'FeatureCollection' as const,
    features: regions.map((region) => ({
      type: 'Feature' as const,
      geometry: {
        type: 'Polygon' as const,
        coordinates: [
          [
            [region.bbox.west, region.bbox.south],
            [region.bbox.east, region.bbox.south],
            [region.bbox.east, region.bbox.north],
            [region.bbox.west, region.bbox.north],
            [region.bbox.west, region.bbox.south],
          ],
        ],
      },
      properties: {
        id: region.id,
        name: region.name,
        total_trees_exact: region.total_trees_exact,
        total_trees_min: region.total_trees_min,
        total_trees_max: region.total_trees_max,
      },
    })),
  };
}
