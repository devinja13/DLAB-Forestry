import { CellResult } from '../store/useOptimizeStore';

// Returns an RGBA tuple [R, G, B, A] based on dominant tree type
export function colorByDominantType(
  cell: CellResult,
): [number, number, number, number] {
  const counts: Record<string, number> = {
    '3gal': cell.trees_3gal,
    '5gal': cell.trees_5gal,
    '10gal': cell.trees_10gal,
  };
  const dominant = Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0];

  switch (dominant) {
    case '3gal':
      return [144, 238, 144, 200]; // light green
    case '5gal':
      return [34, 139, 34, 210]; // medium green
    case '10gal':
      return [0, 80, 0, 220]; // dark green
    default:
      return [100, 180, 100, 180];
  }
}
