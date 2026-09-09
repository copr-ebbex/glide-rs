#!/bin/bash
# Regenerate the vendored crate tarball (Source1) for the Version in the spec.
# Run after every version bump, in the worktree holding the spec. Needs network
# and cargo on the host; the resulting tarball is what makes the rpm build
# offline in mock and Copr.
set -euo pipefail

cd "$(dirname "$0")"
ver=$(awk '/^Version:/{print $2}' glide-rs.spec)
vendor_tarball="glide-rs-$ver-vendor.tar.xz"

rm -rf vendor "glide-$ver"
spectool -g glide-rs.spec
tar xf "glide-rs-$ver.tar.gz"
(cd "glide-$ver" && cargo vendor ../vendor >/dev/null)
XZ_OPT=-T0 tar -caf "$vendor_tarball" vendor
rm -rf vendor "glide-$ver"

echo "wrote $vendor_tarball ($(du -h "$vendor_tarball" | cut -f1))"
