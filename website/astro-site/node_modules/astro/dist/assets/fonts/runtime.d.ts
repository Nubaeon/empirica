import type { ConsumableMap, PreloadData, PreloadFilter } from './types.js';
export declare function createGetFontData({ consumableMap }: {
    consumableMap?: ConsumableMap;
}): (cssVariable: string) => import("./types.js").FontData[];
export declare function filterPreloads(data: Array<PreloadData>, preload: PreloadFilter): Array<PreloadData> | null;
