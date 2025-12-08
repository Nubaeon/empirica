import type { RemoteFontProviderModResolver, RemoteFontProviderResolver } from '../definitions.js';
import type { AstroFontProvider, ResolvedFontProvider } from '../types.js';
export declare class RealRemoteFontProviderResolver implements RemoteFontProviderResolver {
    #private;
    constructor({ root, modResolver, }: {
        root: URL;
        modResolver: RemoteFontProviderModResolver;
    });
    resolve({ entrypoint, config }: AstroFontProvider): Promise<ResolvedFontProvider>;
}
