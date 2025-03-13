#!/bin/bash

echo "🚀 Setting up Python Virtual Environment..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🔧 Setting up pre-commit hooks..."
pre-commit install

echo "✅ Setup complete! Run 'source venv/bin/activate' to activate the environment."