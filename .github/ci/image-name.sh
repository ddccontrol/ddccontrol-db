#!/bin/bash
set -euo pipefail

# Run from the repository root. Hash every input copied into the image.
digest=$(cat .github/ci/Dockerfile .ci/ddccontrol-dbgen.rev \
    .ci/ddccontrol-dbgen.toolchain scripts/dbgen-source-pin.sh | sha256sum)
printf 'ghcr.io/ddccontrol/ddccontrol-db-ci:sha256-%s\n' "${digest%% *}"
