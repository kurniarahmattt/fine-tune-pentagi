FROM nvidia/cuda:12.2.0-devel-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-pip \
    python3.10-dev \
    python3.10-venv \
    git \
    curl \
    wget \
    ninja-build \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /raid/workspace/rahmat/{logs,data,models,.cache/huggingface,axolotl_cache}

# Set working directory
WORKDIR /workspace

# Create non-root user with proper permissions
RUN useradd -m -u 1000 -s /bin/bash user && \
    chown -R user:user /workspace && \
    chown -R user:user /raid/workspace/rahmat

# Switch to user
USER user

# Set environment variables
ENV HF_HOME=/raid/workspace/rahmat/.cache/huggingface
ENV WANDB_DIR=/raid/workspace/rahmat/logs
ENV PYTHONPATH=/workspace
ENV PATH="/workspace/.venv/bin:$PATH"

# Create virtual environment
RUN python3.10 -m venv /workspace/.venv

# Default command
CMD ["/bin/bash"]