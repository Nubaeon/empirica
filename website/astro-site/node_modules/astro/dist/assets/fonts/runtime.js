import { AstroError, AstroErrorData } from "../../core/errors/index.js";
function createGetFontData({ consumableMap }) {
  return function getFontData(cssVariable) {
    if (!consumableMap) {
      throw new AstroError(AstroErrorData.ExperimentalFontsNotEnabled);
    }
    const data = consumableMap.get(cssVariable);
    if (!data) {
      throw new AstroError({
        ...AstroErrorData.FontFamilyNotFound,
        message: AstroErrorData.FontFamilyNotFound.message(cssVariable)
      });
    }
    return data;
  };
}
function filterPreloads(data, preload) {
  if (!preload) {
    return null;
  }
  if (preload === true) {
    return data;
  }
  return data.filter(
    ({ weight, style, subset }) => preload.some((p) => {
      if (p.weight !== void 0 && weight !== void 0 && !checkWeight(p.weight.toString(), weight)) {
        return false;
      }
      if (p.style !== void 0 && p.style !== style) {
        return false;
      }
      if (p.subset !== void 0 && p.subset !== subset) {
        return false;
      }
      return true;
    })
  );
}
function checkWeight(input, target) {
  const trimmedInput = input.trim();
  if (trimmedInput.includes(" ")) {
    return trimmedInput === target;
  }
  if (target.includes(" ")) {
    const [a, b] = target.split(" ");
    const parsedInput = Number.parseInt(input);
    return parsedInput >= Number.parseInt(a) && parsedInput <= Number.parseInt(b);
  }
  return input === target;
}
export {
  createGetFontData,
  filterPreloads
};
