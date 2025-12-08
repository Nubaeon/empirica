import type { FontTypeExtractor } from '../definitions.js';
import type { FontType } from '../types.js';
export declare class RealFontTypeExtractor implements FontTypeExtractor {
    extract(url: string): FontType;
}
