import * as unifont from "unifont";
import { LOCAL_PROVIDER_NAME } from "./constants.js";
import { dedupeFontFaces } from "./core/dedupe-font-faces.js";
import { extractUnifontProviders } from "./core/extract-unifont-providers.js";
import { normalizeRemoteFontFaces } from "./core/normalize-remote-font-faces.js";
import { optimizeFallbacks } from "./core/optimize-fallbacks.js";
import { resolveFamilies } from "./core/resolve-families.js";
import { resolveLocalFont } from "./providers/local.js";
import {
  pickFontFaceProperty,
  renderFontWeight,
  unifontFontFaceDataToProperties
} from "./utils.js";
async function orchestrate({
  families,
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
  createUrlProxy,
  defaults,
  bold,
  stringMatcher
}) {
  let resolvedFamilies = await resolveFamilies({
    families,
    hasher,
    remoteFontProviderResolver,
    localProviderUrlResolver
  });
  const extractedUnifontProvidersResult = extractUnifontProviders({
    families: resolvedFamilies,
    hasher
  });
  resolvedFamilies = extractedUnifontProvidersResult.families;
  const unifontProviders = extractedUnifontProvidersResult.providers;
  const { resolveFont, listFonts } = await unifont.createUnifont(unifontProviders, {
    storage
  });
  const fontFileDataMap = /* @__PURE__ */ new Map();
  const internalConsumableMap = /* @__PURE__ */ new Map();
  const consumableMap = /* @__PURE__ */ new Map();
  const resolvedFamiliesMap = /* @__PURE__ */ new Map();
  for (const family of resolvedFamilies) {
    const key = `${family.cssVariable}:${family.name}:${typeof family.provider === "string" ? family.provider : family.provider.name}`;
    let resolvedFamily = resolvedFamiliesMap.get(key);
    if (!resolvedFamily) {
      if (Array.from(resolvedFamiliesMap.keys()).find((k) => k.startsWith(`${family.cssVariable}:`))) {
        logger.warn(
          "assets",
          `Several font families have been registered for the ${bold(family.cssVariable)} cssVariable but they do not share the same name and provider.`
        );
        logger.warn(
          "assets",
          "These families will not be merged together. The last occurrence will override previous families for this cssVariable. Review your Astro configuration."
        );
      }
      resolvedFamily = {
        family,
        fonts: [],
        fallbacks: family.fallbacks ?? defaults.fallbacks ?? [],
        collectedFonts: [],
        preloadData: []
      };
      resolvedFamiliesMap.set(key, resolvedFamily);
    }
    const urlProxy = createUrlProxy({
      local: family.provider === LOCAL_PROVIDER_NAME,
      hasUrl: (hash) => fontFileDataMap.has(hash),
      saveUrl: ({ hash, url, init }) => {
        fontFileDataMap.set(hash, { url, init });
      },
      savePreload: (preload) => {
        resolvedFamily.preloadData.push(preload);
      },
      saveFontData: (collected) => {
        if (resolvedFamily.fallbacks && resolvedFamily.fallbacks.length > 0 && // If the same data has already been sent for this family, we don't want to have
        // duplicated fallbacks. Such scenario can occur with unicode ranges.
        !resolvedFamily.collectedFonts.some(
          (f) => JSON.stringify(f.data) === JSON.stringify(collected.data)
        )) {
          resolvedFamily.collectedFonts.push(collected);
        }
      },
      cssVariable: family.cssVariable
    });
    if (family.provider === LOCAL_PROVIDER_NAME) {
      const result = resolveLocalFont({
        family,
        urlProxy,
        fontTypeExtractor,
        fontFileReader
      });
      resolvedFamily.fonts.push(...result.fonts);
    } else {
      const result = await resolveFont(
        family.name,
        // We do not merge the defaults, we only provide defaults as a fallback
        {
          weights: family.weights ?? defaults.weights,
          styles: family.styles ?? defaults.styles,
          subsets: family.subsets ?? defaults.subsets,
          fallbacks: family.fallbacks ?? defaults.fallbacks
        },
        // By default, unifont goes through all providers. We use a different approach where
        // we specify a provider per font. Name has been set while extracting unifont providers
        // from families (inside extractUnifontProviders).
        [family.provider.name]
      );
      if (result.fonts.length === 0) {
        logger.warn(
          "assets",
          `No data found for font family ${bold(family.name)}. Review your configuration`
        );
        const availableFamilies = await listFonts([family.provider.name]);
        if (availableFamilies && availableFamilies.length > 0 && !availableFamilies.includes(family.name)) {
          logger.warn(
            "assets",
            `${bold(family.name)} font family cannot be retrieved by the provider. Did you mean ${bold(stringMatcher.getClosestMatch(family.name, availableFamilies))}?`
          );
        }
      }
      resolvedFamily.fonts = dedupeFontFaces(
        resolvedFamily.fonts,
        normalizeRemoteFontFaces({ fonts: result.fonts, urlProxy, fontTypeExtractor })
      );
    }
  }
  for (const {
    family,
    fonts,
    fallbacks,
    collectedFonts,
    preloadData
  } of resolvedFamiliesMap.values()) {
    const consumableMapValue = [];
    let css = "";
    for (const data of fonts) {
      css += cssRenderer.generateFontFace(
        family.nameWithHash,
        unifontFontFaceDataToProperties({
          src: data.src,
          weight: data.weight,
          style: data.style,
          // User settings override the generated font settings. We use a helper function
          // because local and remote providers store this data in different places.
          display: pickFontFaceProperty("display", { data, family }),
          unicodeRange: pickFontFaceProperty("unicodeRange", { data, family }),
          stretch: pickFontFaceProperty("stretch", { data, family }),
          featureSettings: pickFontFaceProperty("featureSettings", { data, family }),
          variationSettings: pickFontFaceProperty("variationSettings", { data, family })
        })
      );
      consumableMapValue.push({
        weight: renderFontWeight(data.weight),
        style: data.style,
        src: data.src.filter((src) => "url" in src).map((src) => ({
          url: src.url,
          format: src.format,
          tech: src.tech
        }))
      });
    }
    const cssVarValues = [family.nameWithHash];
    const optimizeFallbacksResult = await optimizeFallbacks({
      family,
      fallbacks,
      collectedFonts,
      enabled: family.optimizedFallbacks ?? defaults.optimizedFallbacks ?? false,
      systemFallbacksProvider,
      fontMetricsResolver
    });
    if (optimizeFallbacksResult) {
      css += optimizeFallbacksResult.css;
      cssVarValues.push(...optimizeFallbacksResult.fallbacks);
    } else {
      cssVarValues.push(...fallbacks);
    }
    css += cssRenderer.generateCssVariable(family.cssVariable, cssVarValues);
    internalConsumableMap.set(family.cssVariable, { preloadData, css });
    consumableMap.set(family.cssVariable, consumableMapValue);
  }
  return { fontFileDataMap, internalConsumableMap, consumableMap };
}
export {
  orchestrate
};
