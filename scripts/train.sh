#!/bin/bash

set -e

echo "🚀 Starting Qwen3:8B Pentest Fine-tuning on 4x H100 GPUs (Docker Environment)"
echo "📊 Hardware: 4x NVIDIA H100 80GB HBM3"
echo "🎯 Dataset: Security-focused penetration testing data"
echo "🔧 Framework: Axolotl with QLoRA"
echo "💾 Storage: /workspace/ (project directory)"

# Create necessary directories within project directory
mkdir -p /workspace/logs
mkdir -p /workspace/data
mkdir -p /workspace/models
mkdir -p /workspace/.cache/huggingface
mkdir -p /workspace/axolotl_cache

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a /workspace/logs/training.log
}

log "🔧 Installing Axolotl and dependencies..."

# Install system dependencies
sudo apt-get update -qq
sudo apt-get install -y git ninja-build

# Install PyTorch with CUDA 12.2 support (optimized for H100)
log "📦 Installing PyTorch with CUDA 12.2..."
pip install --upgrade pip
MAX_JOBS=32 pip install --upgrade torch==2.3.0 torchvision==0.18.0 torchaudio==2.3.0 --index-url https://download.pytorch.org/whl/cu122

# Install core dependencies
log "📦 Installing core dependencies..."
pip install --upgrade transformers==4.41.0 datasets==2.20.0 accelerate==0.30.1 peft==0.11.0 bitsandbytes==0.43.0
pip install --upgrade wandb huggingface_hub

# Install Axolotl from source (latest version)
log "📦 Installing Axolotl from source..."
rm -rf axolotl
git clone https://github.com/axolotl-ai-cloud/axolotl.git
cd axolotl
pip install -q -U packaging setuptools wheel ninja
MAX_JOBS=32 pip install --no-build-isolation -e .
python scripts/cutcrossentropy_install.py | sh

# Install Flash Attention for H100 optimization
log "📦 Installing Flash Attention for H100 optimization..."
MAX_JOBS=32 pip uninstall flash-attn -y
MAX_JOBS=32 pip install -q flash-attn==2.8.1 --no-build-isolation

# Install additional optimizations
log "📦 Installing additional optimizations..."
pip install --upgrade -q 'optree>=0.13.0'
pip install --upgrade pyarrow

cd ..

# Verify installations
log "✅ Verifying installations..."
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.version.cuda}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
python -c "import axolotl; print(f'Axolotl: {axolotl.__version__}')"

# Security enhancement and data preparation
log "🔒 Running security enhancement..."
python src/security_enhancement.py

log "📊 Running data filtering..."
python src/data_filtering.py

log "🔄 Running data augmentation..."
python src/data_augmentation.py

# Display dataset statistics
log "📈 Dataset Statistics:"
echo "Original: $(wc -l < ./data/training_data.jsonl) examples" | tee -a /workspace/logs/training.log
echo "Filtered: $(wc -l < ./data/filtered_data.jsonl) examples" | tee -a /workspace/logs/training.log
echo "Augmented: $(wc -l < ./data/augmented_training_data.jsonl) examples" | tee -a /workspace/logs/training.log

# Validate dataset format
log "🔍 Validating dataset format..."
python src/validate_dataset.py

# Set environment variables for optimal H100 performance
export CUDA_VISIBLE_DEVICES=0,1,2,3
export NCCL_DEBUG=INFO
export NCCL_IB_DISABLE=0
export NCCL_P2P_DISABLE=0
export OMP_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false

# Update config to use project directories
log "🔧 Updating configuration for project storage..."
sed -i 's|output_dir: ./qwen3-finetuned|output_dir: ./models/qwen3-finetuned|g' config/qwen3_h100_4gpu_config.yml
sed -i 's|logging_dir: ./logs|logging_dir: ./logs|g' config/qwen3_h100_4gpu_config.yml

# Launch distributed training across 4 H100 GPUs
log "🚀 Starting distributed training on 4x H100 GPUs..."
log "📋 Training Configuration:"
log "   - Model: Qwen3:8B with QLoRA"
log "   - GPUs: 4x H100 80GB"
log "   - Batch Size: 32 (micro_batch_size=4, gradient_accumulation=8)"
log "   - Sequence Length: 8192"
log "   - Learning Rate: 0.0002"
log "   - Epochs: 8"
log "   - Output: ./models/qwen3-finetuned"
log "   - Logs: ./logs"

# Start training with comprehensive logging
torchrun \
    --nproc_per_node=4 \
    --master_port=29500 \
    -m axolotl.cli.train \
    config/qwen3_h100_4gpu_config.yml \
    2>&1 | tee -a /workspace/logs/training.log

log "✅ Training completed successfully!"
log "📁 Model saved to: ./models/qwen3-finetuned"
log "📊 Training logs saved to: ./logs"

# Display final model information
if [ -d "./models/qwen3-finetuned" ]; then
    log "📋 Final Model Information:"
    ls -la ./models/qwen3-finetuned/
    echo "Model size: $(du -sh ./models/qwen3-finetuned/ | cut -f1)" | tee -a /workspace/logs/training.log
fi

log "🎉 Fine-tuning pipeline completed successfully!"
log "💾 All data, logs, and models saved to project directory:"
log "   - Models: ./models/"
log "   - Logs: ./logs/"
log "   - Cache: ./.cache/"
log "   - Data: ./data/"