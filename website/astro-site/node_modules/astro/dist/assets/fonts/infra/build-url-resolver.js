import { fileExtension, joinPaths, prependForwardSlash } from "../../../core/path.js";
import { getAssetsPrefix } from "../../utils/getAssetsPrefix.js";
import { createPlaceholderURL, stringifyPlaceholderURL } from "../../utils/url.js";
class BuildUrlResolver {
  #resources = /* @__PURE__ */ new Set();
  #base;
  #assetsPrefix;
  #searchParams;
  constructor({
    base,
    assetsPrefix,
    searchParams
  }) {
    this.#base = base;
    this.#assetsPrefix = assetsPrefix;
    this.#searchParams = searchParams;
  }
  resolve(hash) {
    const prefix = this.#assetsPrefix ? getAssetsPrefix(fileExtension(hash), this.#assetsPrefix) : void 0;
    let urlPath;
    if (prefix) {
      this.#resources.add(prefix);
      urlPath = joinPaths(prefix, this.#base, hash);
    } else {
      this.#resources.add("'self'");
      urlPath = prependForwardSlash(joinPaths(this.#base, hash));
    }
    const url = createPlaceholderURL(urlPath);
    this.#searchParams.forEach((value, key) => {
      url.searchParams.set(key, value);
    });
    return stringifyPlaceholderURL(url);
  }
  get cspResources() {
    return Array.from(this.#resources);
  }
}
export {
  BuildUrlResolver
};
