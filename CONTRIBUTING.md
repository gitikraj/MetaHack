# Contributing to MetaHackUI

Thank you for your interest in contributing! Here's how to get started.

## Setup Development Environment

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/MetaHackUI.git
cd MetaHackUI
```

### 2. Create Virtual Environment
```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n metahackui python=3.10
conda activate metahackui
```

### 3. Install Dependencies
```bash
# Core dependencies
pip install -r requirements.txt

# Project-specific dependencies
pip install -r project/requirements.txt

# Development dependencies (optional)
pip install black flake8 pytest jupyter
```

### 4. Verify Installation
```bash
python -c "import torch; print(torch.__version__)"
python -c "import transformers; print(transformers.__version__)"
```

## Project Structure

```
MetaHackUI/
├── agents/              # Multi-agent implementations
├── openenv/             # Gymnasium-compatible environment
├── rl/                  # Reinforcement learning training
├── project/             # SFT training scripts
├── dataset/             # Data files
├── scripts/             # Utility scripts
├── web/                 # Web interface (if applicable)
├── colab_combined_training.ipynb  # Google Colab training notebook
└── README.md            # Project documentation
```

## Development Workflow

### Running SFT Training Locally
```bash
cd project
python train.py
```

### Running RL Training Locally
```bash
python rl/train.py
```

### Running on Google Colab
1. Upload `colab_combined_training.ipynb` to Colab
2. Update `REPO_URL` to your repository
3. Select GPU runtime and run all cells

## Code Standards

### Python Style
- Follow PEP 8
- Use type hints where possible
- Keep functions focused and testable
- Add docstrings to public functions

### Example:
```python
def process_incident(logs: Dict[str, Any], code: str) -> Dict[str, Any]:
    """
    Process security incident data.
    
    Args:
        logs: Dictionary of security logs
        code: Source code to analyze
        
    Returns:
        Dictionary with analysis results
    """
    # Implementation
    pass
```

## Making Changes

### Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages
```bash
# Good
git commit -m "Add LoRA configuration to SFT training"
git commit -m "Fix PPO reward calculation in environment"

# Bad
git commit -m "fixes"
git commit -m "changes"
```

### Pull Request Checklist
- [ ] Code follows PEP 8 style guide
- [ ] Added docstrings to new functions
- [ ] Updated README if needed
- [ ] Tested locally before pushing
- [ ] No API keys or credentials in commits
- [ ] Models and large files not included

## Testing

### Run Quick Tests
```bash
# Test imports
python -c "from agents import *; from openenv import *; print('✅ Imports OK')"

# Test environment creation
python -c "from openenv import CyberMultiAgentEnv; print('✅ Environment OK')"
```

### Create Test Files
Place tests in `tests/` directory (if creating):
```bash
tests/
├── __init__.py
├── test_agents.py
├── test_environment.py
└── test_training.py
```

## Common Issues

### CUDA/GPU Issues
```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"

# If False, ensure NVIDIA drivers are installed
nvidia-smi
```

### ImportError on openenv
```bash
# Add project to Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/MetaHackUI"
```

### Out of Memory during Training
```python
# Reduce in project/train.py
per_device_train_batch_size = 1      # Already minimal
gradient_accumulation_steps = 4      # Reduce from 8
max_length = 256                     # Reduce from 512
```

## Documentation

### Update README.md
If you add major features, update the main README with:
- Feature description
- Usage example
- Performance metrics (if applicable)

### Add Docstrings
```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """
    Brief description.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When this error occurs
    """
```

## Questions?

- Check existing issues and discussions
- Review documentation in README.md and guides/
- Create an issue with detailed description

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Happy contributing! 🚀
