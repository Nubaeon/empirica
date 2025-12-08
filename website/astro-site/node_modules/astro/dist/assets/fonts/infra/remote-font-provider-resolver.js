import { AstroError, AstroErrorData } from "../../../core/errors/index.js";
import { resolveEntrypoint } from "../utils.js";
class RealRemoteFontProviderResolver {
  #root;
  #modResolver;
  constructor({
    root,
    modResolver
  }) {
    this.#root = root;
    this.#modResolver = modResolver;
  }
  #validateMod({
    mod,
    entrypoint
  }) {
    try {
      if (typeof mod !== "object" || mod === null) {
        throw new Error(`Expected an object for the module, but received ${typeof mod}.`);
      }
      if (typeof mod.provider !== "function") {
        throw new Error(`Invalid provider export in module, expected a function.`);
      }
      return {
        provider: mod.provider
      };
    } catch (cause) {
      throw new AstroError(
        {
          ...AstroErrorData.CannotLoadFontProvider,
          message: AstroErrorData.CannotLoadFontProvider.message(entrypoint)
        },
        { cause }
      );
    }
  }
  async resolve({ entrypoint, config }) {
    const id = resolveEntrypoint(this.#root, entrypoint.toString()).href;
    const mod = await this.#modResolver.resolve(id);
    const { provider } = this.#validateMod({
      mod,
      entrypoint: id
    });
    return { config, provider };
  }
}
export {
  RealRemoteFontProviderResolver
};
