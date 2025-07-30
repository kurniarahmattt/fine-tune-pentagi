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

# Set working directory
WORKDIR /workspace

# Create necessary directories within workspace
RUN mkdir -p /workspace/logs /workspace/data /workspace/models /workspace/.cache/huggingface /workspace/axolotl_cache

# Create non-root user with proper permissions
RUN useradd -m -u 1000 -s /bin/bash user && \
    chown -R user:user /workspace

# Switch to user
USER user

# Set environment variables
ENV HF_HOME=/workspace/.cache/huggingface
ENV WANDB_DIR=/workspace/logs
ENV PYTHONPATH=/workspace
ENV PATH="/workspace/.venv/bin:$PATH"

# Create virtual environment
RUN python3.10 -m venv /workspace/.venv

# Default command
CMD ["/bin/bash"]