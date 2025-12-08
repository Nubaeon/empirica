import type { LocalProviderUrlResolver } from '../definitions.js';
export declare class RequireLocalProviderUrlResolver implements LocalProviderUrlResolver {
    #private;
    constructor({ root, intercept, }: {
        root: URL;
        intercept?: ((path: string) => void) | undefined;
    });
    resolve(input: string): string;
}
