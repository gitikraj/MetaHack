@echo off
REM Setup script for MetaHackUI on Windows

echo.
echo 🚀 MetaHackUI Setup Script
echo ==========================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.9+
    exit /b 1
)

echo ✅ Python found:
python --version

REM Create virtual environment
if not exist "venv" (
    echo.
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Activate venv
echo.
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

REM Install core dependencies
echo 📦 Installing core dependencies...
pip install -r requirements.txt

REM Install project dependencies
echo 📦 Installing project dependencies...
pip install -r project\requirements.txt

REM Optional: development dependencies
echo.
set /p install_dev="Install development dependencies? (black, flake8, pytest) [y/N]: "
if /i "%install_dev%"=="y" (
    pip install black flake8 pytest jupyter
    echo ✅ Dev dependencies installed
)

REM Verify installation
echo.
echo 🧪 Verifying installation...
python -c "import torch; print(f'✅ PyTorch: {torch.__version__}')" 2>nul || echo ⚠️ PyTorch check failed
python -c "import transformers; print(f'✅ Transformers: {transformers.__version__}')" 2>nul || echo ⚠️ Transformers check failed
python -c "from agents import *; print('✅ Agents imported')" 2>nul || echo ⚠️ Agents import failed
python -c "from openenv import *; print('✅ OpenEnv imported')" 2>nul || echo ⚠️ OpenEnv import failed

echo.
echo 🎉 Setup complete!
echo.
echo 📚 Next steps:
echo 1. Run Training: python project\train.py
echo 2. For RL: python rl\train.py
echo 3. See COLAB_QUICKSTART.md for Colab training
echo.
echo 📖 Documentation:
echo    - README.md - Project overview
echo    - CONTRIBUTING.md - Contribution guidelines
echo    - COLAB_QUICKSTART.md - Colab training guide
echo.
pause
