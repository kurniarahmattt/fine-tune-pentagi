# 🐳 Docker Training Guide for Qwen3:8B Security Fine-tuning

## 📋 Overview

This guide provides step-by-step instructions for running Qwen3:8B security fine-tuning in a Docker environment with all data, logs, and cache stored in `/raid/workspace/rahmat/`.

## 🎯 Requirements

### **Hardware**
- **GPUs**: 4x NVIDIA H100 80GB HBM3
- **Storage**: Sufficient space in `/raid/workspace/rahmat/`
- **Docker**: Docker and Docker Compose installed
- **NVIDIA Docker**: nvidia-docker2 runtime

### **Software**
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **NVIDIA Docker**: nvidia-docker2
- **CUDA**: 12.2 support

## 📁 Directory Structure

After setup, your `/raid/workspace/rahmat/` will contain:

```
/raid/workspace/rahmat/
├── project/              # Project files
├── logs/                 # Training logs and monitoring
├── data/                 # Dataset files
├── models/               # Fine-tuned models
├── .cache/               # HuggingFace cache
│   └── huggingface/      # Model cache
└── axolotl_cache/        # Axolotl cache
```

## 🚀 Quick Start

### **Step 1: Setup Docker Environment**

```bash
# Run the setup script
bash scripts/setup_docker.sh
```

This script will:
- Create raid directory structure
- Set proper permissions
- Copy project files
- Build Docker image

### **Step 2: Start Training**

```bash
# Navigate to raid project directory
cd /raid/workspace/rahmat/project

# Start training
docker-compose up
```

### **Step 3: Monitor Training**

```bash
# In a new terminal, run the monitoring script
bash scripts/monitor_training.sh
```

## 📊 Detailed Instructions

### **1. Pre-Training Setup**

#### **Verify GPU Availability**
```bash
# Check GPU status
nvidia-smi

# Verify Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

#### **Setup Raid Directory**
```bash
# Create directory structure
sudo mkdir -p /raid/workspace/rahmat/{logs,data,models,.cache/huggingface,axolotl_cache}

# Set permissions
sudo chown -R $USER:$USER /raid/workspace/rahmat/
sudo chmod -R 755 /raid/workspace/rahmat/
```

#### **Build Docker Image**
```bash
# Build the training image
docker build -t qwen3-axolotl:latest .
```

### **2. Training Execution**

#### **Option 1: Using Docker Compose (Recommended)**
```bash
# Start training with docker-compose
cd /raid/workspace/rahmat/project
docker-compose up
```

#### **Option 2: Manual Docker Run**
```bash
# Run training container manually
docker run --rm \
  --gpus '"device=0,1,2,3"' \
  --name qwen3-finetune \
  -v /raid/workspace/rahmat:/raid/workspace/rahmat \
  -v $(pwd):/workspace \
  -e CUDA_VISIBLE_DEVICES=0,1,2,3 \
  -e HF_HOME=/raid/workspace/rahmat/.cache/huggingface \
  -e WANDB_DIR=/raid/workspace/rahmat/logs \
  qwen3-axolotl:latest \
  bash scripts/train.sh
```

### **3. Monitoring and Logs**

#### **Real-time Monitoring**
```bash
# Run monitoring script
bash scripts/monitor_training.sh
```

#### **Check Training Status**
```bash
# Check if container is running
docker ps | grep qwen3-finetune

# View container logs
docker logs -f qwen3-finetune
```

#### **Monitor GPU Usage**
```bash
# Real-time GPU monitoring
watch -n 1 nvidia-smi

# Detailed GPU info
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv
```

#### **Check Training Logs**
```bash
# View training logs
tail -f /raid/workspace/rahmat/logs/training.log

# View recent logs
tail -n 50 /raid/workspace/rahmat/logs/training.log
```

### **4. Data and Cache Management**

#### **Check Disk Usage**
```bash
# Check raid directory usage
du -sh /raid/workspace/rahmat/*

# Monitor disk space
df -h /raid/workspace/rahmat/
```

#### **Cache Management**
```bash
# Check HuggingFace cache size
du -sh /raid/workspace/rahmat/.cache/huggingface

# Clear cache if needed (be careful!)
# rm -rf /raid/workspace/rahmat/.cache/huggingface/*
```

### **5. Model Output**

#### **Check Model Progress**
```bash
# List saved models
ls -la /raid/workspace/rahmat/models/

# Check model size
du -sh /raid/workspace/rahmat/models/*
```

#### **Model Information**
```bash
# Check final model
ls -la /raid/workspace/rahmat/models/qwen3-finetuned/

# Model size
du -sh /raid/workspace/rahmat/models/qwen3-finetuned/
```

## 🔧 Troubleshooting

### **Common Issues**

#### **1. GPU Not Available**
```bash
# Check GPU availability
nvidia-smi

# Verify Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi

# Install nvidia-docker2 if needed
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

#### **2. Permission Issues**
```bash
# Fix raid directory permissions
sudo chown -R $USER:$USER /raid/workspace/rahmat/
sudo chmod -R 755 /raid/workspace/rahmat/
```

#### **3. Container Fails to Start**
```bash
# Check Docker logs
docker logs qwen3-finetune

# Check available disk space
df -h /raid/workspace/rahmat/

# Restart container
docker-compose down
docker-compose up
```

#### **4. Out of Memory**
```bash
# Check GPU memory usage
nvidia-smi

# Reduce batch size in config
# Edit config/qwen3_h100_4gpu_config.yml
# Change micro_batch_size: 4 to micro_batch_size: 2
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
# Reduce sequence length in config
# sequence_len: 4096 instead of 8192

# Increase gradient accumulation
# gradient_accumulation_steps: 16 instead of 8
```

## 📈 Expected Performance

### **Training Metrics**
- **Duration**: 6-8 hours on 4x H100
- **Memory Usage**: ~75GB per GPU
- **Effective Batch Size**: 128
- **Model Size**: ~8.1B parameters

### **Storage Requirements**
- **Dataset**: ~40MB
- **Cache**: ~50-100GB (HuggingFace models)
- **Logs**: ~100MB
- **Final Model**: ~16GB
- **Total**: ~150-200GB

## 🎯 Post-Training

### **Model Evaluation**
```bash
# Test the fine-tuned model
cd /raid/workspace/rahmat/project
python scripts/inference.py
```

### **Model Deployment**
```bash
# Copy model to deployment location
cp -r /raid/workspace/rahmat/models/qwen3-finetuned /path/to/deployment/
```

### **Cleanup**
```bash
# Stop training container
docker-compose down

# Remove Docker image (optional)
docker rmi qwen3-axolotl:latest
```

## 📞 Support

### **Useful Commands**
```bash
# Check container status
docker ps -a | grep qwen3

# View container logs
docker logs qwen3-finetune

# Enter container (for debugging)
docker exec -it qwen3-finetune bash

# Check GPU usage
nvidia-smi

# Monitor disk usage
du -sh /raid/workspace/rahmat/*
```

### **Log Locations**
- **Training Logs**: `/raid/workspace/rahmat/logs/training.log`
- **Docker Logs**: `docker logs qwen3-finetune`
- **WandB Logs**: `/raid/workspace/rahmat/logs/`

---

## 🎉 Ready to Train!

**Your Docker environment is configured for optimal performance on 4x H100 GPUs with persistent storage in `/raid/workspace/rahmat/`.**

**Start training with:**
```bash
bash scripts/setup_docker.sh
cd /raid/workspace/rahmat/project
docker-compose up
``` 