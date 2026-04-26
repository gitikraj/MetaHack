#!/bin/bash
# Setup script for MetaHackUI on Linux/Mac

set -e  # Exit on error

echo "🚀 MetaHackUI Setup Script"
echo "========================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.9+"
    exit 1
fi

echo "✅ Python3 found: $(python3 --version)"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate venv
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install core dependencies
echo "📦 Installing core dependencies..."
pip install -r requirements.txt

# Install project dependencies
echo "📦 Installing project dependencies..."
pip install -r project/requirements.txt

# Optional: development dependencies
read -p "Install development dependencies? (black, flake8, pytest) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip install black flake8 pytest jupyter
    echo "✅ Dev dependencies installed"
fi

# Verify installation
echo ""
echo "🧪 Verifying installation..."
python -c "import torch; print(f'✅ PyTorch: {torch.__version__}')" || echo "⚠️ PyTorch check failed"
python -c "import transformers; print(f'✅ Transformers: {transformers.__version__}')" || echo "⚠️ Transformers check failed"
python -c "from agents import *; print('✅ Agents imported')" || echo "⚠️ Agents import failed"
python -c "from openenv import *; print('✅ OpenEnv imported')" || echo "⚠️ OpenEnv import failed"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📚 Next steps:"
echo "1. Activate venv: source venv/bin/activate"
echo "2. Run training: python project/train.py"
echo "3. See COLAB_QUICKSTART.md for Colab training"
echo ""
echo "📖 Documentation:"
echo "   - README.md - Project overview"
echo "   - CONTRIBUTING.md - Contribution guidelines"
echo "   - COLAB_QUICKSTART.md - Colab training guide"
