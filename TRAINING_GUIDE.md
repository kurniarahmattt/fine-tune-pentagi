# 🚀 Qwen3:8B Security Fine-tuning Training Guide

## 📋 Overview

This guide provides step-by-step instructions for fine-tuning Qwen3:8B on security/penetration testing data using **4x NVIDIA H100 80GB GPUs** with Axolotl framework.

## 🎯 Hardware Requirements

### **Recommended Setup**
- **GPUs**: 4x NVIDIA H100 80GB HBM3
- **CPU**: 32+ cores recommended
- **RAM**: 128GB+ system memory
- **Storage**: 300GB+ SSD/NVMe storage
- **Network**: High-speed interconnect (InfiniBand recommended)

### **Minimum Setup**
- **GPUs**: 2x NVIDIA H100 80GB
- **CPU**: 16+ cores
- **RAM**: 64GB system memory
- **Storage**: 150GB+ SSD storage

## 📁 Project Structure

```
training-pentest/
├── config/
│   ├── qwen3_h100_4gpu_config.yml    # Main training config for 4x H100
│   └── qwen3_config.yml              # Original config
├── data/
│   ├── training_data.jsonl           # Original dataset (3,627 examples)
│   ├── filtered_data.jsonl           # Quality-filtered dataset (2,979 examples)
│   └── augmented_training_data.jsonl # Final augmented dataset (4,715 examples)
├── scripts/
│   ├── train.sh                      # Main training script
│   └── validate_config.py            # Configuration validation
├── src/
│   ├── security_enhancement.py       # Security tokenizer enhancement
│   ├── data_filtering.py             # Dataset quality filtering
│   ├── data_augmentation.py          # Dataset augmentation
│   └── validate_dataset.py           # Dataset validation
├── tokenizer_security/               # Enhanced security tokenizer
└── logs/                             # Training logs (created during training)
```

## 🔧 Pre-Training Setup

### **1. Environment Preparation**

```bash
# Activate virtual environment
source .venv/bin/activate

# Install system dependencies (if needed)
sudo apt-get update
sudo apt-get install -y git ninja-build
```

### **2. Configuration Validation**

Before running training, validate your setup:

```bash
# Run comprehensive validation
python scripts/validate_config.py
```

This will check:
- ✅ Python version compatibility
- ✅ GPU availability and CUDA version
- ✅ Required dependencies
- ✅ Dataset files and format
- ✅ Tokenizer configuration
- ✅ Axolotl configuration
- ✅ Disk space and system memory

### **3. Dataset Verification**

Ensure your datasets are ready:

```bash
# Check dataset statistics
echo "Dataset Statistics:"
wc -l data/training_data.jsonl
wc -l data/filtered_data.jsonl  
wc -l data/augmented_training_data.jsonl

# Validate dataset format
python src/validate_dataset.py
```

## 🚀 Training Execution

### **Option 1: Full Training Pipeline (Recommended)**

```bash
# Run complete training pipeline
bash scripts/train.sh
```

This script will:
1. 🔧 Install Axolotl and all dependencies
2. 🔒 Run security enhancement
3. 📊 Run data filtering and augmentation
4. 🚀 Launch distributed training on 4x H100 GPUs
5. 📈 Monitor training progress
6. 💾 Save the fine-tuned model

### **Option 2: Manual Step-by-Step**

If you prefer manual control:

```bash
# 1. Install dependencies
pip install --upgrade torch==2.3.0 torchvision==0.18.0 torchaudio==2.3.0 --index-url https://download.pytorch.org/whl/cu122
pip install --upgrade transformers==4.41.0 datasets==2.20.0 accelerate==0.30.1 peft==0.11.0 bitsandbytes==0.43.0

# 2. Install Axolotl
rm -rf axolotl
git clone https://github.com/axolotl-ai-cloud/axolotl.git
cd axolotl
pip install -q -U packaging setuptools wheel ninja
MAX_JOBS=32 pip install --no-build-isolation -e .
python scripts/cutcrossentropy_install.py | sh
MAX_JOBS=32 pip install -q flash-attn==2.8.1 --no-build-isolation
cd ..

# 3. Run data preparation
python src/security_enhancement.py
python src/data_filtering.py
python src/data_augmentation.py

# 4. Start training
torchrun --nproc_per_node=4 --master_port=29500 -m axolotl.cli.train config/qwen3_h100_4gpu_config.yml
```

## ⚙️ Configuration Details

### **Training Configuration (`config/qwen3_h100_4gpu_config.yml`)**

#### **Model Settings**
- **Base Model**: Qwen/Qwen3-8B
- **Adapter**: QLoRA (LoRA rank: 256, alpha: 512)
- **Sequence Length**: 8192 tokens
- **Flash Attention**: Enabled for H100 optimization

#### **Hardware Optimization**
- **Precision**: bfloat16 (optimized for H100)
- **TF32**: Enabled
- **Gradient Checkpointing**: Enabled
- **Torch Compile**: Enabled with Inductor backend

#### **Distributed Training**
- **GPUs**: 4x H100
- **Strategy**: FSDP (Fully Sharded Data Parallel)
- **Micro Batch Size**: 4 per GPU
- **Gradient Accumulation**: 8 steps
- **Effective Batch Size**: 128 (4 × 8 × 4)

#### **Training Parameters**
- **Learning Rate**: 0.0002
- **Epochs**: 8
- **Warmup Steps**: 100
- **Evaluation**: Every 100 steps
- **Model Saving**: Every 100 steps

## 📊 Expected Performance

### **Training Metrics**
- **Training Time**: ~6-8 hours on 4x H100
- **Memory Usage**: ~75GB per GPU
- **Effective Batch Size**: 128
- **Gradient Updates**: ~300-400 per epoch

### **Model Performance**
- **Base Model Size**: 8B parameters
- **LoRA Adapters**: ~67M parameters
- **Final Model Size**: ~8.1B parameters
- **Inference Memory**: ~16GB per GPU

## 📈 Monitoring Training

### **Real-time Monitoring**

```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# Monitor training logs
tail -f logs/training.log

# Monitor system resources
htop
```

### **Weights & Biases Integration**

The training automatically logs to Weights & Biases:
- **Project**: `qwen3-security-finetuning`
- **Metrics**: Loss, learning rate, gradient norms
- **System**: GPU utilization, memory usage

## 🛠️ Troubleshooting

### **Common Issues**

#### **1. CUDA Out of Memory**
```bash
# Reduce micro_batch_size in config
micro_batch_size: 2  # Instead of 4
```

#### **2. Slow Training**
```bash
# Check GPU utilization
nvidia-smi

# Verify NCCL communication
export NCCL_DEBUG=INFO
```

#### **3. Model Loading Issues**
```bash
# Clear cache and restart
rm -rf ~/.cache/huggingface
rm -rf ./last_run_prepared
```

### **Performance Optimization**

#### **For Maximum Speed**
```bash
# Set optimal environment variables
export CUDA_VISIBLE_DEVICES=0,1,2,3
export NCCL_IB_DISABLE=0
export NCCL_P2P_DISABLE=0
export OMP_NUM_THREADS=8
```

#### **For Memory Efficiency**
```bash
# Reduce sequence length
sequence_len: 4096  # Instead of 8192

# Increase gradient accumulation
gradient_accumulation_steps: 16  # Instead of 8
```

## 📁 Output Files

After training completion:

```
qwen3-finetuned/
├── adapter_config.json          # LoRA adapter configuration
├── adapter_model.safetensors    # LoRA weights
├── config.json                  # Model configuration
├── generation_config.json       # Generation settings
├── pytorch_model.bin.index.json # Model index
├── special_tokens_map.json      # Special tokens
├── tokenizer_config.json        # Tokenizer settings
└── tokenizer.json              # Tokenizer files
```

## 🔍 Model Evaluation

### **Quick Test**

```bash
# Load and test the model
python scripts/inference.py
```

### **Comprehensive Evaluation**

```bash
# Run security-specific evaluation
python -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained('./qwen3-finetuned')
tokenizer = AutoTokenizer.from_pretrained('./qwen3-finetuned')

# Test security prompts
prompts = [
    'How to identify IDOR vulnerabilities?',
    'Explain SQL injection techniques',
    'What tools are used for network scanning?'
]

for prompt in prompts:
    inputs = tokenizer(prompt, return_tensors='pt')
    outputs = model.generate(**inputs, max_length=200)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f'Q: {prompt}')
    print(f'A: {response}\\n')
"
```

## 🎯 Next Steps

After successful training:

1. **Model Deployment**: Deploy the fine-tuned model for inference
2. **Performance Testing**: Evaluate on security-specific benchmarks
3. **Integration**: Integrate with security tools and workflows
4. **Continuous Training**: Set up automated retraining pipeline

## 📞 Support

For issues or questions:
1. Check the training logs in `./logs/`
2. Verify configuration with `python scripts/validate_config.py`
3. Review this guide for troubleshooting steps
4. Check Axolotl documentation for advanced configuration

---

**🎉 Happy Training!** 🎉 