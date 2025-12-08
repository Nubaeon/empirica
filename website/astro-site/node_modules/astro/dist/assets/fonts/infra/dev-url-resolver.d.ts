import type { UrlResolver } from '../definitions.js';
export declare class DevUrlResolver implements UrlResolver {
    #private;
    constructor({ base, searchParams, }: {
        base: string;
        searchParams: URLSearchParams;
    });
    resolve(hash: string): string;
    get cspResources(): Array<string>;
}
