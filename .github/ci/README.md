# Prebuilt CI image

Both `check-db` and `build-and-install` use the Linux amd64 image
`ghcr.io/ddccontrol/ddccontrol-db-ci`, matching the `ubuntu-24.04` runners.
PR checks only pull the image. They never build images, install system packages
or Rust toolchains, or download Cargo dependencies. Cargo runs in offline mode.
There is deliberately no fallback that installs dependencies during a PR check.

The image contains:

- ddccontrol 3.3.0 built from the immutable revision in `Dockerfile`;
- Make, bmake, Autotools, gettext, Perl XML support and archive/build tools;
- the Rust release in `.ci/ddccontrol-dbgen.toolchain`;
- the exact generator source in `.ci/ddccontrol-dbgen.rev`, its release binary,
  downloaded crates and precompiled producer/shared-format/runtime tests.

The validator is built in a separate stage so its compiler artifacts are not
included. The generator source and tests remain in `/opt/ddccontrol-dbgen` so
PR checks can run them against the current database, including the full
XML/CBOR differential check. All existing build/install regression checks remain.
The release workflow continues to use the source-build composite action.

## Updating the image

Run `bash .github/ci/image-name.sh` from the repository root to calculate the
`sha256-<hash>` tag. The hash covers the Dockerfile, both generator pins and the
pin validation script: all files used to build the image. Changing any of these
selects a new image; changing database profiles does not.

The `CI Image` workflow builds, smoke-tests and publishes on relevant pushes to
master, weekly and on manual dispatch. It never runs for pull requests. Weekly
builds refresh Ubuntu packages under the same tag.

Before opening a PR that changes image inputs, a maintainer must build, test and
publish the new tag so its checks can pull it. Push the branch, then dispatch the
`CI Image` workflow on that branch (once this workflow exists on master):

```sh
gh workflow run ci-image.yml --ref <branch>
```

Wait for publication before opening the PR. Alternatively, build on a Linux
amd64 host from the repository root:

```sh
image=$(bash .github/ci/image-name.sh)
docker build --platform linux/amd64 --pull \
  --label org.opencontainers.image.source=https://github.com/ddccontrol/ddccontrol-db \
  --tag "$image" --file .github/ci/Dockerfile .
docker run --rm --network none --platform linux/amd64 -v "$PWD:/src:ro" "$image" \
  bash -c 'set -euo pipefail; cp -a /src /tmp/ddccontrol-db; cd /tmp/ddccontrol-db; git config --global --add safe.directory "$PWD"; make check-db; ./autogen.sh; ./configure --prefix=/usr; make; make check; make check-controls; make check-cbor'
# Authenticate to ghcr.io with an account allowed to publish this package.
docker push "$image"
```

The package is linked to this repository and inherits Actions access. Jobs use
GitHub's automatic `GITHUB_TOKEN` with `packages: read` to pull it; no personal
access token or repository secret is required. Fork pull request tokens retain
read access to the base repository. The publishing workflow uses `packages:
write`. Package visibility can remain private, matching the companion project's
CI images.
