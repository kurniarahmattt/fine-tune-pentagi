#!/bin/bash

set -e

echo "🚀 Setting up Docker environment for Qwen3:8B Security Fine-tuning"
echo "📊 Target: 4x NVIDIA H100 80GB GPUs"
echo "💾 Storage: /raid/workspace/rahmat/"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "🔧 Creating raid directory structure..."

# Create raid directory structure
sudo mkdir -p /raid/workspace/rahmat/{logs,data,models,.cache/huggingface,axolotl_cache}

# Set proper permissions
sudo chown -R $USER:$USER /raid/workspace/rahmat/
sudo chmod -R 755 /raid/workspace/rahmat/

log "📁 Directory structure created:"
echo "   /raid/workspace/rahmat/"
echo "   ├── logs/           # Training logs and monitoring"
echo "   ├── data/           # Dataset files"
echo "   ├── models/         # Fine-tuned models"
echo "   ├── .cache/         # HuggingFace cache"
echo "   └── axolotl_cache/  # Axolotl cache"

log "📋 Copying project files to raid directory..."

# Copy project files to raid directory
cp -r . /raid/workspace/rahmat/project/

# Copy dataset files
cp -r data/* /raid/workspace/rahmat/data/ 2>/dev/null || true

# Copy tokenizer files
cp -r tokenizer_security /raid/workspace/rahmat/ 2>/dev/null || true

log "🔍 Checking GPU availability..."
nvidia-smi

log "🐳 Building Docker image..."

# Build Docker image
docker build -t qwen3-axolotl:latest .

log "✅ Docker image built successfully!"

log "📋 Docker setup complete!"
log ""
log "🎯 Next steps:"
log "1. Navigate to raid directory: cd /raid/workspace/rahmat/project"
log "2. Start training: docker-compose up"
log "3. Monitor logs: tail -f /raid/workspace/rahmat/logs/training.log"
log "4. Check GPU usage: watch -n 1 nvidia-smi"
log ""
log "📁 Important directories:"
log "   - Project: /raid/workspace/rahmat/project"
log "   - Logs: /raid/workspace/rahmat/logs"
log "   - Models: /raid/workspace/rahmat/models"
log "   - Data: /raid/workspace/rahmat/data"
log "   - Cache: /raid/workspace/rahmat/.cache" 