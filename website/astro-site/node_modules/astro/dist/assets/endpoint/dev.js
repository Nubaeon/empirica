import { root } from "astro:config/server";
import { readFile } from "node:fs/promises";
import os from "node:os";
import { fileURLToPath } from "node:url";
import { isParentDirectory } from "@astrojs/internal-helpers/path";
import { handleImageRequest, loadRemoteImage } from "./shared.js";
function replaceFileSystemReferences(src) {
  return os.platform().includes("win32") ? src.replace(/^\/@fs\//, "") : src.replace(/^\/@fs/, "");
}
async function loadLocalImage(src, url) {
  if (src.startsWith("/@fs/")) {
    src = replaceFileSystemReferences(src);
    if (!isParentDirectory(fileURLToPath(root), src)) {
      return void 0;
    }
  }
  if (isParentDirectory(fileURLToPath(root), src)) {
    try {
      return await readFile(src);
    } catch {
      return void 0;
    }
  } else {
    const sourceUrl = new URL(src, url.origin);
    if (sourceUrl.origin !== url.origin) {
      return void 0;
    }
    return loadRemoteImage(sourceUrl);
  }
}
const GET = async ({ request }) => {
  if (!import.meta.env.DEV) {
    console.error("The dev image endpoint can only be used in dev mode.");
    return new Response("Invalid endpoint", { status: 500 });
  }
  try {
    return await handleImageRequest({ request, loadLocalImage });
  } catch (err) {
    console.error("Could not process image request:", err);
    return new Response(`Could not process image request: ${err}`, {
      status: 500
    });
  }
};
export {
  GET
};
