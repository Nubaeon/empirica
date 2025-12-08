class BuildRemoteFontProviderModResolver {
  async resolve(id) {
    return await import(id);
  }
}
export {
  BuildRemoteFontProviderModResolver
};
