class RealDataCollector {
  #hasUrl;
  #saveUrl;
  #savePreload;
  #saveFontData;
  constructor({
    hasUrl,
    saveUrl,
    savePreload,
    saveFontData
  }) {
    this.#hasUrl = hasUrl;
    this.#saveUrl = saveUrl;
    this.#savePreload = savePreload;
    this.#saveFontData = saveFontData;
  }
  collect({
    hash,
    url,
    init,
    preload,
    data
  }) {
    if (!this.#hasUrl(hash)) {
      this.#saveUrl({ hash, url, init });
      if (preload) {
        this.#savePreload(preload);
      }
    }
    this.#saveFontData({ hash, url, data, init });
  }
}
export {
  RealDataCollector
};
