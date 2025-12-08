class RemoteUrlProxyContentResolver {
  // Passthrough, the remote provider URL is enough
  resolve(url) {
    return url;
  }
}
export {
  RemoteUrlProxyContentResolver
};
