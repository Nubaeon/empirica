import { mkdirSync, writeFileSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { isAbsolute } from "node:path";
import { fileURLToPath } from "node:url";
import colors from "piccolore";
import { getAlgorithm, shouldTrackCspHashes } from "../../core/csp/common.js";
import { generateCspDigest } from "../../core/encryption.js";
import { collectErrorMetadata } from "../../core/errors/dev/utils.js";
import { AstroError, AstroErrorData, isAstroError } from "../../core/errors/index.js";
import { formatErrorMessage } from "../../core/messages.js";
import { appendForwardSlash, joinPaths, prependForwardSlash } from "../../core/path.js";
import { getClientOutputDirectory } from "../../prerender/utils.js";
import {
  ASSETS_DIR,
  CACHE_DIR,
  DEFAULTS,
  RESOLVED_VIRTUAL_MODULE_ID,
  VIRTUAL_MODULE_ID
} from "./constants.js";
import { BuildRemoteFontProviderModResolver } from "./infra/build-remote-font-provider-mod-resolver.js";
import { BuildUrlProxyHashResolver } from "./infra/build-url-proxy-hash-resolver.js";
import { BuildUrlResolver } from "./infra/build-url-resolver.js";
import { CachedFontFetcher } from "./infra/cached-font-fetcher.js";
import { CapsizeFontMetricsResolver } from "./infra/capsize-font-metrics-resolver.js";
import { RealDataCollector } from "./infra/data-collector.js";
import { DevServerRemoteFontProviderModResolver } from "./infra/dev-remote-font-provider-mod-resolver.js";
import { DevUrlProxyHashResolver } from "./infra/dev-url-proxy-hash-resolver.js";
import { DevUrlResolver } from "./infra/dev-url-resolver.js";
import { RealFontTypeExtractor } from "./infra/font-type-extractor.js";
import { FontaceFontFileReader } from "./infra/fontace-font-file-reader.js";
import { LevenshteinStringMatcher } from "./infra/levenshtein-string-matcher.js";
import { LocalUrlProxyContentResolver } from "./infra/local-url-proxy-content-resolver.js";
import { MinifiableCssRenderer } from "./infra/minifiable-css-renderer.js";
import { RealRemoteFontProviderResolver } from "./infra/remote-font-provider-resolver.js";
import { RemoteUrlProxyContentResolver } from "./infra/remote-url-proxy-content-resolver.js";
import { RequireLocalProviderUrlResolver } from "./infra/require-local-provider-url-resolver.js";
import { RealSystemFallbacksProvider } from "./infra/system-fallbacks-provider.js";
import { UnstorageFsStorage } from "./infra/unstorage-fs-storage.js";
import { RealUrlProxy } from "./infra/url-proxy.js";
import { XxhashHasher } from "./infra/xxhash-hasher.js";
import { orchestrate } from "./orchestrate.js";
function fontsPlugin({ settings, sync, logger }) {
  if (!settings.config.experimental.fonts) {
    return {
      name: "astro:fonts:fallback",
      resolveId(id) {
        if (id === VIRTUAL_MODULE_ID) {
          return RESOLVED_VIRTUAL_MODULE_ID;
        }
      },
      load(id) {
        if (id === RESOLVED_VIRTUAL_MODULE_ID) {
          return {
            code: ""
          };
        }
      }
    };
  }
  const assetsDir = prependForwardSlash(
    appendForwardSlash(joinPaths(settings.config.build.assets, ASSETS_DIR))
  );
  const baseUrl = joinPaths(settings.config.base, assetsDir);
  let fontFileDataMap = null;
  let internalConsumableMap = null;
  let consumableMap = null;
  let isBuild;
  let fontFetcher = null;
  let fontTypeExtractor = null;
  const cleanup = () => {
    internalConsumableMap = null;
    consumableMap = null;
    fontFileDataMap = null;
    fontFetcher = null;
  };
  async function initialize({
    cacheDir,
    modResolver,
    cssRenderer,
    urlResolver,
    createHashResolver
  }) {
    const { root } = settings.config;
    const hasher = await XxhashHasher.create();
    const remoteFontProviderResolver = new RealRemoteFontProviderResolver({
      root,
      modResolver
    });
    const pathsToWarn = /* @__PURE__ */ new Set();
    const localProviderUrlResolver = new RequireLocalProviderUrlResolver({
      root,
      intercept: (path) => {
        if (path.startsWith(fileURLToPath(settings.config.publicDir))) {
          if (pathsToWarn.has(path)) {
            return;
          }
          pathsToWarn.add(path);
          logger.warn(
            "assets",
            `Found a local font file ${JSON.stringify(path)} in the \`public/\` folder. To avoid duplicated files in the build output, move this file into \`src/\``
          );
        }
      }
    });
    const storage = new UnstorageFsStorage({ base: cacheDir });
    const systemFallbacksProvider = new RealSystemFallbacksProvider();
    fontFetcher = new CachedFontFetcher({ storage, fetch, readFile });
    const fontMetricsResolver = new CapsizeFontMetricsResolver({ fontFetcher, cssRenderer });
    fontTypeExtractor = new RealFontTypeExtractor();
    const fontFileReader = new FontaceFontFileReader();
    const stringMatcher = new LevenshteinStringMatcher();
    const res = await orchestrate({
      families: settings.config.experimental.fonts,
      hasher,
      remoteFontProviderResolver,
      localProviderUrlResolver,
      storage,
      cssRenderer,
      systemFallbacksProvider,
      fontMetricsResolver,
      fontTypeExtractor,
      fontFileReader,
      logger,
      createUrlProxy: ({ local, cssVariable, ...params }) => {
        const dataCollector = new RealDataCollector(params);
        const contentResolver = local ? new LocalUrlProxyContentResolver() : new RemoteUrlProxyContentResolver();
        return new RealUrlProxy({
          urlResolver,
          hashResolver: createHashResolver({ hasher, contentResolver }),
          dataCollector,
          cssVariable
        });
      },
      defaults: DEFAULTS,
      bold: colors.bold,
      stringMatcher
    });
    fontFileDataMap = res.fontFileDataMap;
    internalConsumableMap = res.internalConsumableMap;
    consumableMap = res.consumableMap;
    if (shouldTrackCspHashes(settings.config.experimental.csp)) {
      const algorithm = getAlgorithm(settings.config.experimental.csp);
      for (const { css } of internalConsumableMap.values()) {
        settings.injectedCsp.styleHashes.push(await generateCspDigest(css, algorithm));
      }
      for (const resource of urlResolver.cspResources) {
        settings.injectedCsp.fontResources.add(resource);
      }
    }
  }
  return {
    name: "astro:fonts",
    config(_, { command }) {
      isBuild = command === "build";
    },
    async buildStart() {
      if (isBuild) {
        await initialize({
          cacheDir: new URL(CACHE_DIR, settings.config.cacheDir),
          modResolver: new BuildRemoteFontProviderModResolver(),
          cssRenderer: new MinifiableCssRenderer({ minify: true }),
          urlResolver: new BuildUrlResolver({
            base: baseUrl,
            assetsPrefix: settings.config.build.assetsPrefix,
            searchParams: settings.adapter?.client?.assetQueryParams ?? new URLSearchParams()
          }),
          createHashResolver: (dependencies) => new BuildUrlProxyHashResolver(dependencies)
        });
      }
    },
    async configureServer(server) {
      await initialize({
        // In dev, we cache fonts data in .astro so it can be easily inspected and cleared
        cacheDir: new URL(CACHE_DIR, settings.dotAstroDir),
        modResolver: new DevServerRemoteFontProviderModResolver({ server }),
        cssRenderer: new MinifiableCssRenderer({ minify: false }),
        urlResolver: new DevUrlResolver({
          base: baseUrl,
          searchParams: settings.adapter?.client?.assetQueryParams ?? new URLSearchParams()
        }),
        createHashResolver: (dependencies) => new DevUrlProxyHashResolver(dependencies)
      });
      const localPaths = [...fontFileDataMap.values()].filter(({ url }) => isAbsolute(url)).map((v) => v.url);
      server.watcher.on("change", (path) => {
        if (localPaths.includes(path)) {
          logger.info("assets", "Font file updated");
          server.restart();
        }
      });
      server.watcher.on("unlink", (path) => {
        if (localPaths.includes(path)) {
          logger.warn(
            "assets",
            `The font file ${JSON.stringify(path)} referenced in your config has been deleted. Restore the file or remove this font from your configuration if it is no longer needed.`
          );
        }
      });
      server.middlewares.use(assetsDir, async (req, res, next) => {
        if (!req.url) {
          return next();
        }
        const hash = req.url.slice(1);
        const associatedData = fontFileDataMap?.get(hash);
        if (!associatedData) {
          return next();
        }
        res.setHeader("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0");
        res.setHeader("Pragma", "no-cache");
        res.setHeader("Expires", 0);
        try {
          const data = await fontFetcher.fetch({ hash, ...associatedData });
          res.setHeader("Content-Length", data.length);
          res.setHeader("Content-Type", `font/${fontTypeExtractor.extract(hash)}`);
          res.end(data);
        } catch (err) {
          logger.error("assets", "Cannot download font file");
          if (isAstroError(err)) {
            logger.error(
              "SKIP_FORMAT",
              formatErrorMessage(collectErrorMetadata(err), logger.level() === "debug")
            );
          }
          res.statusCode = 500;
          res.end();
        }
      });
    },
    resolveId(id) {
      if (id === VIRTUAL_MODULE_ID) {
        return RESOLVED_VIRTUAL_MODULE_ID;
      }
    },
    load(id) {
      if (id === RESOLVED_VIRTUAL_MODULE_ID) {
        return {
          code: `
						export const internalConsumableMap = new Map(${JSON.stringify(Array.from(internalConsumableMap?.entries() ?? []))});
						export const consumableMap = new Map(${JSON.stringify(Array.from(consumableMap?.entries() ?? []))});
					`
        };
      }
    },
    async buildEnd() {
      if (sync || settings.config.experimental.fonts.length === 0) {
        cleanup();
        return;
      }
      try {
        const dir = getClientOutputDirectory(settings);
        const fontsDir = new URL(`.${assetsDir}`, dir);
        try {
          mkdirSync(fontsDir, { recursive: true });
        } catch (cause) {
          throw new AstroError(AstroErrorData.UnknownFilesystemError, { cause });
        }
        if (fontFileDataMap) {
          logger.info(
            "assets",
            `Copying fonts (${fontFileDataMap.size} file${fontFileDataMap.size === 1 ? "" : "s"})...`
          );
          await Promise.all(
            Array.from(fontFileDataMap.entries()).map(async ([hash, associatedData]) => {
              const data = await fontFetcher.fetch({ hash, ...associatedData });
              try {
                writeFileSync(new URL(hash, fontsDir), data);
              } catch (cause) {
                throw new AstroError(AstroErrorData.UnknownFilesystemError, { cause });
              }
            })
          );
        }
      } finally {
        cleanup();
      }
    }
  };
}
export {
  fontsPlugin
};
