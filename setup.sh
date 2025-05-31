#!/bin/bash
# Development setup script for NnennaAI

set -e  # Exit on error

echo "🧠 Setting up NnennaAI development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if (( $(echo "$python_version < $required_version" | bc -l) )); then
    echo "❌ Error: Python $required_version or higher is required (found $python_version)"
    exit 1
fi

echo "✅ Python $python_version detected"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "♻️  Using existing virtual environment"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install package in editable mode with all dependencies
echo "📦 Installing NnennaAI in development mode..."
pip install -e ".[all]"

# Create .env from example if it doesn't exist
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Don't forget to add your API keys to .env!"
fi

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p .nai/runs
mkdir -p .nai/chroma
mkdir -p data
mkdir -p docs

# Run a quick test
echo "🧪 Testing installation..."
python -c "from modules import RunEngine; print('✅ Modules imported successfully')"
nai --version

echo ""
echo "🎉 Setup complete! NnennaAI is ready for development."
echo ""
echo "To activate the environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To get started:"
echo "  nai init my-first-project"
echo "  cd my-first-project"
echo "  nai ingest ./docs"
echo "  nai run 'What is NnennaAI?'"
echo ""
echo "Happy building! 🚀"