class DevUrlProxyHashResolver {
  #hasher;
  #contentResolver;
  constructor({
    hasher,
    contentResolver
  }) {
    this.#hasher = hasher;
    this.#contentResolver = contentResolver;
  }
  #formatWeight(weight) {
    if (Array.isArray(weight)) {
      return weight.join("-");
    }
    if (typeof weight === "number") {
      return weight.toString();
    }
    return weight?.replace(/\s+/g, "-");
  }
  resolve({
    cssVariable,
    data,
    originalUrl,
    type
  }) {
    return [
      cssVariable.slice(2),
      this.#formatWeight(data.weight),
      data.style,
      data.subset,
      `${this.#hasher.hashString(this.#contentResolver.resolve(originalUrl))}.${type}`
    ].filter(Boolean).join("-");
  }
}
export {
  DevUrlProxyHashResolver
};
