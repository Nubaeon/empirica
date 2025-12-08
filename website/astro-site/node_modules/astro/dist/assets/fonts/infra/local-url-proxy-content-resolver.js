import { readFileSync } from "node:fs";
import { AstroError, AstroErrorData } from "../../../core/errors/index.js";
class LocalUrlProxyContentResolver {
  resolve(url) {
    try {
      return url + readFileSync(url, "utf-8");
    } catch (cause) {
      throw new AstroError(AstroErrorData.UnknownFilesystemError, { cause });
    }
  }
}
export {
  LocalUrlProxyContentResolver
};
