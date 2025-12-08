import { renderFontWeight } from "../utils.js";
class RealUrlProxy {
  #hashResolver;
  #dataCollector;
  #urlResolver;
  #cssVariable;
  constructor({
    hashResolver,
    dataCollector,
    urlResolver,
    cssVariable
  }) {
    this.#hashResolver = hashResolver;
    this.#dataCollector = dataCollector;
    this.#urlResolver = urlResolver;
    this.#cssVariable = cssVariable;
  }
  proxy({
    url: originalUrl,
    type,
    data,
    collectPreload,
    init
  }) {
    const hash = this.#hashResolver.resolve({
      cssVariable: this.#cssVariable,
      data,
      originalUrl,
      type
    });
    const url = this.#urlResolver.resolve(hash);
    this.#dataCollector.collect({
      url: originalUrl,
      hash,
      preload: collectPreload ? {
        url,
        type,
        weight: renderFontWeight(data.weight),
        style: data.style,
        subset: data.subset
      } : null,
      data,
      init
    });
    return url;
  }
}
export {
  RealUrlProxy
};
