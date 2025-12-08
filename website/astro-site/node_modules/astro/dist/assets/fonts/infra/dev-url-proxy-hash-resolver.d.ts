import type { Hasher, ProxyData, UrlProxyContentResolver, UrlProxyHashResolver } from '../definitions.js';
import type { FontType } from '../types.js';
export declare class DevUrlProxyHashResolver implements UrlProxyHashResolver {
    #private;
    constructor({ hasher, contentResolver, }: {
        hasher: Hasher;
        contentResolver: UrlProxyContentResolver;
    });
    resolve({ cssVariable, data, originalUrl, type, }: {
        originalUrl: string;
        type: FontType;
        cssVariable: string;
        data: ProxyData;
    }): string;
}
