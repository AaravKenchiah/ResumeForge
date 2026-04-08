#!/usr/bin/env bash
set -euo pipefail

python3 -m http.server 4173 -d frontend
