#!/bin/bash

echo "=== PDF OCR 和 AI 分析系统启动脚本 ==="

# 检查Python环境
echo "检查Python环境..."
./.venv/bin/python --version

# 安装依赖
echo "安装Python依赖包..."
./.venv/bin/pip install -r requirements.txt

# 创建必要的文件夹
echo "创建必要的文件夹..."
mkdir -p uploads
mkdir -p results
mkdir -p temp_images

# 启动Flask应用
echo "启动Web服务器..."
echo "服务器将在 http://localhost:5000 启动"
echo "按 Ctrl+C 停止服务器"
echo ""

./.venv/bin/python app.py
