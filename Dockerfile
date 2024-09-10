# Build stage
ARG BASE_IMAGE=ubuntu:20.04
FROM ${BASE_IMAGE} as builder

LABEL builder=true
SHELL ["/bin/bash", "-c"]

ENV DEBIAN_FRONTEND=noninteractive
ENV CARGO_REGISTRIES_CRATES_IO_PROTOCOL=sparse 
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# Install necessary libraries for Rust execution
RUN apt-get update && \
    apt-get install --assume-yes make build-essential git clang curl libssl-dev llvm libudev-dev protobuf-compiler && \
    rm -rf /var/lib/apt/lists/*

# Install cargo and Rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Set up Rust toolchains
RUN rustup update nightly && \
    rustup update stable && \
    rustup target add wasm32-unknown-unknown --toolchain nightly && \
    rustup target add wasm32-unknown-unknown --toolchain stable

# Clone and build subtensor
RUN git clone --depth 1 https://github.com/opentensor/subtensor.git /subtensor
WORKDIR /subtensor
RUN cargo build --release --features pow-faucet

# Runtime stage
FROM ${BASE_IMAGE} AS subtensor

# Install runtime dependencies
RUN apt-get update && \
    apt-get install --assume-yes libssl-dev && \
    rm -rf /var/lib/apt/lists/*

# Alice ports
EXPOSE 30334
EXPOSE 9946
EXPOSE 9934

WORKDIR /subtensor/

# Copy built binary and script from builder stage
COPY --from=builder /subtensor/target/release/node-subtensor ./target/release/
COPY localnet.sh ./scripts/localnet.sh

# Run subtensor
CMD ["bash", "./scripts/localnet.sh"]