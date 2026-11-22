#!/bin/sh
# SPDX-License-Identifier: MIT
set -eu
cd "$(dirname "$0")/.."
exec python3 -B tools/prepublish.py "$@"
