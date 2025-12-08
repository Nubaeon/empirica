import type { ViteDevServer } from 'vite';
import type { RemoteFontProviderModResolver } from '../definitions.js';
export declare class DevServerRemoteFontProviderModResolver implements RemoteFontProviderModResolver {
    #private;
    constructor({ server, }: {
        server: ViteDevServer;
    });
    resolve(id: string): Promise<any>;
}
