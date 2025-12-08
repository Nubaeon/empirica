import { fileURLToPath } from "node:url";
import { resolveEntrypoint } from "../utils.js";
class RequireLocalProviderUrlResolver {
  #root;
  // TODO: remove when stabilizing
  #intercept;
  constructor({
    root,
    intercept
  }) {
    this.#root = root;
    this.#intercept = intercept;
  }
  resolve(input) {
    const path = fileURLToPath(resolveEntrypoint(this.#root, input));
    this.#intercept?.(path);
    return path;
  }
}
export {
  RequireLocalProviderUrlResolver
};
