FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        autoconf automake autopoint build-essential ca-certificates cargo \
        gettext git intltool libglib2.0-dev libtool libxml2-dev pkg-config rustc \
    && rm -rf /var/lib/apt/lists/*

# Older ddccontrol versions can accept unresolved value IDs (issue #427).
# Keep the source immutable: the image tag hashes this Dockerfile, including the pin.
RUN git init /build \
    && cd /build \
    && git remote add origin https://github.com/ddccontrol/ddccontrol.git \
    && git fetch --depth=1 origin 2b6c3d64388e05aced148d60d493b1e29563b756 \
    && git checkout --detach FETCH_HEAD \
    && test "$(git rev-parse HEAD)" = 2b6c3d64388e05aced148d60d493b1e29563b756 \
    && ./autogen.sh \
    && ./configure --disable-gnome --disable-nls \
    && make -j"$(nproc)" \
    && make install DESTDIR=/install

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libglib2.0-0t64 libxml2 make \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install/usr/local/ /usr/local/
RUN ldconfig

# Build and installation checks run entirely from preinstalled dependencies.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        autoconf automake bmake build-essential ca-certificates curl gettext \
        git libxml-parser-perl xz-utils \
    && rm -rf /var/lib/apt/lists/*

ENV RUSTUP_HOME=/opt/rustup \
    CARGO_HOME=/opt/cargo
ENV PATH=/opt/cargo/bin:/opt/ddccontrol-dbgen/target/release:$PATH

COPY .ci/ddccontrol-dbgen.rev .ci/ddccontrol-dbgen.toolchain scripts/dbgen-source-pin.sh /opt/ci/
RUN /opt/ci/dbgen-source-pin.sh /opt/ci/ddccontrol-dbgen.rev /opt/ci/ddccontrol-dbgen.toolchain \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o /tmp/rustup-init.sh \
    && sh /tmp/rustup-init.sh -y --profile minimal --default-toolchain "$(cat /opt/ci/ddccontrol-dbgen.toolchain)" \
    && rm /tmp/rustup-init.sh \
    && git init /opt/ddccontrol-dbgen \
    && cd /opt/ddccontrol-dbgen \
    && git remote add origin https://github.com/ddccontrol/ddccontrol.git \
    && git fetch --depth=1 origin "$(cat /opt/ci/ddccontrol-dbgen.rev)" \
    && git checkout --detach FETCH_HEAD \
    && test "$(git rev-parse HEAD)" = "$(cat /opt/ci/ddccontrol-dbgen.rev)" \
    && cargo build --locked --release -p ddccontrol-dbgen \
    && cargo test --locked --no-run -p ddccontrol-dbgen -p ddccontrol-db-format \
    && cargo test --locked --no-run -p ddccontrol-db --features gettext

# PR checks must not download crates, even if a cache entry is missing.
ENV CARGO_NET_OFFLINE=true
