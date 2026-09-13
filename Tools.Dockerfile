FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends clang-format \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
ENTRYPOINT ["clang-format"]
