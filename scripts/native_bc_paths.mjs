// Match complete native-run directories before deriving any metadata member path.
export const formalRoot = '/private/tmp/topolab-native-bc-run-20261127-r3';
const publicRoot = /^\/private\/tmp\/topolab-native-bc-public-20261127-r3-[a-z0-9][a-z0-9-]{0,47}$/;
export function entryRoot(root, publicOnly) {
  return publicOnly === true ? publicRoot.test(root) : root === formalRoot;
}
export function underEntryRoot(path) {
  const root = path.split('/').slice(0, 4).join('/');
  return path.startsWith(root + '/') && (root === formalRoot || publicRoot.test(root));
}

export function rowFixture(root) {
  if (!publicRoot.test(root)) return null;
  return ['rows-positive','rows-failure','rows-prerow'].find(mode=>root.endsWith('-'+mode)) ?? null;
}
