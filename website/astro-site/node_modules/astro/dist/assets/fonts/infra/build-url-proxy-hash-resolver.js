class BuildUrlProxyHashResolver {
  #hasher;
  #contentResolver;
  constructor({
    hasher,
    contentResolver
  }) {
    this.#hasher = hasher;
    this.#contentResolver = contentResolver;
  }
  resolve({
    originalUrl,
    type
  }) {
    return `${this.#hasher.hashString(this.#contentResolver.resolve(originalUrl))}.${type}`;
  }
}
export {
  BuildUrlProxyHashResolver
};
