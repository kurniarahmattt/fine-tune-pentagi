#!/bin/bash

echo "📊 Qwen3:8B Security Fine-tuning Monitor"
echo "🎯 Target: 4x NVIDIA H100 80GB GPUs"
echo "💾 Storage: /raid/workspace/rahmat/"
echo ""

# Function to check if training is running
check_training() {
    if docker ps | grep -q "qwen3-finetune"; then
        echo "✅ Training container is running"
        return 0
    else
        echo "❌ Training container is not running"
        return 1
    fi
}

# Function to show GPU usage
show_gpu_usage() {
    echo "🔍 GPU Usage:"
    nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits | while IFS=, read -r index name util mem_used mem_total temp; do
        echo "   GPU $index ($name): ${util}% util, ${mem_used}MB/${mem_total}MB, ${temp}°C"
    done
}

# Function to show training logs
show_logs() {
    echo "📋 Recent Training Logs:"
    if [ -f "/raid/workspace/rahmat/logs/training.log" ]; then
        tail -n 20 /raid/workspace/rahmat/logs/training.log
    else
        echo "   No training logs found yet"
    fi
}

# Function to show disk usage
show_disk_usage() {
    echo "💾 Disk Usage:"
    echo "   /raid/workspace/rahmat/:"
    du -sh /raid/workspace/rahmat/* 2>/dev/null | while read size path; do
        echo "     $size - $(basename $path)"
    done
}

# Function to show model progress
show_model_progress() {
    echo "🤖 Model Progress:"
    if [ -d "/raid/workspace/rahmat/models" ]; then
        ls -la /raid/workspace/rahmat/models/ 2>/dev/null || echo "   No models found yet"
    else
        echo "   Models directory not found"
    fi
}

# Function to show cache status
show_cache_status() {
    echo "📦 Cache Status:"
    if [ -d "/raid/workspace/rahmat/.cache/huggingface" ]; then
        cache_size=$(du -sh /raid/workspace/rahmat/.cache/huggingface 2>/dev/null | cut -f1)
        echo "   HuggingFace Cache: $cache_size"
    else
        echo "   HuggingFace Cache: Not found"
    fi
}

# Main monitoring loop
while true; do
    clear
    echo "🕐 $(date)"
    echo "=========================================="
    
    check_training
    echo ""
    
    show_gpu_usage
    echo ""
    
    show_disk_usage
    echo ""
    
    show_cache_status
    echo ""
    
    show_model_progress
    echo ""
    
    show_logs
    echo ""
    
    echo "🔄 Refreshing in 30 seconds... (Ctrl+C to exit)"
    echo "=========================================="
    
    sleep 30
done 