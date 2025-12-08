class DevServerRemoteFontProviderModResolver {
  #server;
  constructor({
    server
  }) {
    this.#server = server;
  }
  async resolve(id) {
    return await this.#server.ssrLoadModule(id);
  }
}
export {
  DevServerRemoteFontProviderModResolver
};
