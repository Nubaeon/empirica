import type { DataCollector, ProxyData } from '../definitions.js';
import type { CreateUrlProxyParams, FontFileData, PreloadData } from '../types.js';
export declare class RealDataCollector implements DataCollector {
    #private;
    constructor({ hasUrl, saveUrl, savePreload, saveFontData, }: Pick<CreateUrlProxyParams, 'hasUrl' | 'saveUrl' | 'savePreload' | 'saveFontData'>);
    collect({ hash, url, init, preload, data, }: FontFileData & {
        data: ProxyData;
        preload: PreloadData | null;
    }): void;
}
