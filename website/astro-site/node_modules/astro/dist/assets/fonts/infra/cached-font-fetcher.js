import { isAbsolute } from "node:path";
import { AstroError, AstroErrorData } from "../../../core/errors/index.js";
import { cache } from "../utils.js";
class CachedFontFetcher {
  #storage;
  #fetch;
  #readFile;
  constructor({
    storage,
    fetch,
    readFile
  }) {
    this.#storage = storage;
    this.#fetch = fetch;
    this.#readFile = readFile;
  }
  async fetch({ hash, url, init }) {
    return await cache(this.#storage, hash, async () => {
      try {
        if (isAbsolute(url)) {
          return await this.#readFile(url);
        }
        const response = await this.#fetch(url, init ?? void 0);
        if (!response.ok) {
          throw new Error(`Response was not successful, received status code ${response.status}`);
        }
        return Buffer.from(await response.arrayBuffer());
      } catch (cause) {
        throw new AstroError(
          {
            ...AstroErrorData.CannotFetchFontFile,
            message: AstroErrorData.CannotFetchFontFile.message(url)
          },
          { cause }
        );
      }
    });
  }
}
export {
  CachedFontFetcher
};
