#!/usr/bin/env sh
set -eu

for target in help up down logs status smoke test; do
  if ! make -n "$target" >/dev/null 2>&1; then
    echo "Expected make target '$target' to be available." >&2
    exit 1
  fi
done

echo "Runtime command interface is available."
