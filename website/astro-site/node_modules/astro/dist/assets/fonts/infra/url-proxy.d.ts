import type { DataCollector, ProxyData, UrlProxy, UrlProxyHashResolver, UrlResolver } from '../definitions.js';
import type { FontFileData, FontType } from '../types.js';
export declare class RealUrlProxy implements UrlProxy {
    #private;
    constructor({ hashResolver, dataCollector, urlResolver, cssVariable, }: {
        hashResolver: UrlProxyHashResolver;
        dataCollector: DataCollector;
        urlResolver: UrlResolver;
        cssVariable: string;
    });
    proxy({ url: originalUrl, type, data, collectPreload, init, }: Pick<FontFileData, 'url' | 'init'> & {
        type: FontType;
        collectPreload: boolean;
        data: ProxyData;
    }): string;
}
