import type { RemoteFontProviderModResolver } from '../definitions.js';
export declare class BuildRemoteFontProviderModResolver implements RemoteFontProviderModResolver {
    resolve(id: string): Promise<any>;
}
