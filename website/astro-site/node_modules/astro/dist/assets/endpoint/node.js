import { outDir } from "astro:assets";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { isParentDirectory } from "@astrojs/internal-helpers/path";
import { handleImageRequest } from "./shared.js";
async function loadLocalImage(src, url) {
  const idx = url.pathname.indexOf("/_image");
  if (idx > 0) {
    src = src.slice(idx);
  }
  if (!URL.canParse("." + src, outDir)) {
    return void 0;
  }
  const fileUrl = new URL("." + src, outDir);
  if (fileUrl.protocol !== "file:") {
    return void 0;
  }
  if (!isParentDirectory(fileURLToPath(outDir), fileURLToPath(fileUrl))) {
    return void 0;
  }
  try {
    return await readFile(fileUrl);
  } catch {
    return void 0;
  }
}
const GET = async ({ request }) => {
  try {
    return await handleImageRequest({ request, loadLocalImage });
  } catch (err) {
    console.error("Could not process image request:", err);
    return new Response("Internal Server Error", {
      status: 500
    });
  }
};
export {
  GET
};
