#!/bin/bash
set -euo pipefail

# Bazel genrules run with this restricted PATH, excluding Homebrew and /usr/sbin.
if ! command -v ccache >/dev/null 2>&1; then
    brew install ccache
fi
ccache_bin="$(command -v ccache)"
sudo mkdir -p /usr/local/bin
if ! env PATH=/bin:/usr/bin:/usr/local/bin ccache --version >/dev/null 2>&1; then
    sudo ln -s "$ccache_bin" /usr/local/bin/ccache
fi
if ! env PATH=/bin:/usr/bin:/usr/local/bin sysctl -n hw.ncpu >/dev/null 2>&1; then
    sudo ln -s /usr/sbin/sysctl /usr/local/bin/sysctl
fi
env -i PATH=/bin:/usr/bin:/usr/local/bin ccache --version
env -i PATH=/bin:/usr/bin:/usr/local/bin sysctl -n hw.ncpu

xcodebuild -downloadComponent MetalToolchain
probe_dir="$(mktemp -d)"
trap 'rm -rf "$probe_dir"' EXIT
printf '#include <metal_stdlib>\nusing namespace metal;\nkernel void ayu_probe(device uint *out [[buffer(0)]], uint id [[thread_position_in_grid]]) { out[id] = id; }\n' > "$probe_dir/probe.metal"
xcrun --sdk iphoneos metal -c -target air64-apple-ios15.0 "$probe_dir/probe.metal" -o "$probe_dir/probe.air"
test -s "$probe_dir/probe.air"
echo 'Metal and restricted-PATH build tools passed preflight.'
