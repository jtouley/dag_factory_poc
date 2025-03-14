#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "🔍 Checking system dependencies..."

# 🍺 Check & Install Homebrew if missing
if ! command_exists brew; then
    echo "🚨 Homebrew not found! Please install Homebrew first: https://brew.sh/"
    exit 1
fi

# 🐍 Ensure Python3 and Virtual Environment Module Exist
if ! command_exists python3; then
    echo "🚨 Python3 is not installed! Please install it first."
    exit 1
fi

if ! python3 -m ensurepip --default-pip >/dev/null 2>&1; then
    echo "🚨 Python3's venv module is missing! Installing..."
    python3 -m ensurepip
fi

# 🐳 Check & Install Docker if not installed
if ! command_exists docker; then
    echo "🚨 Docker not found! Installing via Homebrew..."
    brew install --cask docker
    echo "✅ Docker installed! Please start Docker Desktop manually."
else
    echo "✅ Docker is already installed."
fi

# 🔄 Check & Install Docker Compose
if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    echo "🚨 Docker Compose not found! Installing via Homebrew..."
    brew install docker-compose
    echo "✅ Docker Compose installed."
else
    echo "✅ Docker Compose is already installed."
fi

# 🚀 Check if the virtual environment exists
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment 'venv' already exists."
    read -p "🔄 Do you want to delete and recreate it? (y/N): " choice
    case "$choice" in 
      y|Y ) 
        echo "🗑 Removing existing virtual environment..."
        rm -rf venv
        echo "✅ Old virtual environment removed."
        ;;
      * ) 
        echo "⏩ Keeping existing virtual environment."
        exit 0
        ;;
    esac
fi

# 🛠 Create a new virtual environment
echo "🚀 Creating Python Virtual Environment..."
python3 -m venv venv
source venv/bin/activate

# 📦 Install local dependencies
echo "📦 Installing local dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 🧹 Flush and reinstall pre-commit
echo "🗑 Flushing pre-commit cache..."
pre-commit clean
rm -rf ~/.cache/pre-commit

echo "🔧 Setting up pre-commit hooks..."
pip install pre-commit
pre-commit install

echo "✅ Setup complete! Run 'source venv/bin/activate' to activate the environment."