# Training on Google Colab - Complete Guide

## Setup Steps

### 1. Prepare Your Project for Colab
Before running in Colab, ensure:
- Your project is in a GitHub repo OR ready to upload
- All dependencies are in `requirements.txt` and `project/requirements.txt`
- Your data files (train.jsonl, cases.json) are accessible

### 2. Use the Provided Colab Notebooks
Two notebooks are provided:
- `colab_sft_training.ipynb` - For supervised fine-tuning (project/train.py)
- `colab_rl_training.ipynb` - For RL training (rl/train.py)

### 3. Key Colab Considerations

#### GPU Selection
- Go to **Runtime** → **Change runtime type** → Select **T4** or **L4** GPU
- Colab free tier: T4 (16GB VRAM)
- Colab Pro: L4 (24GB VRAM)

#### Drive Mounting
```python
from google.colab import drive
drive.mount('/content/drive')
```

#### Package Installation
```bash
!pip install -q transformers datasets peft accelerate bitsandbytes trl torch gymnasium stable-baselines3
```

### 4. Data Handling Options

**Option A: GitHub (Recommended)**
```bash
!git clone https://github.com/YOUR_USERNAME/MetaHackUI.git
%cd MetaHackUI
```

**Option B: Google Drive**
- Upload project folder to Drive
- Mount and navigate to it

**Option C: Direct Upload**
- Use Colab file upload UI

### 5. Output & Visualization
All notebooks include:
- **Real-time loss curves** with matplotlib
- **Training metrics dashboard** with TensorBoard (optional)
- **Model checkpoints** saved to Drive
- **Results summary** exported as JSON/CSV

## SFT Training Features

✅ Automatic loss tracking  
✅ Gradient accumulation visualization  
✅ Token/step metrics  
✅ Model card generation  
✅ Auto-save to Drive  

## RL Training Features

✅ Reward curves  
✅ Episode length tracking  
✅ Policy parameter updates  
✅ Evaluation metrics  
✅ Checkpoint management  

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CUDA OOM | Reduce `per_device_train_batch_size`, increase `gradient_accumulation_steps` |
| Slow training | Use T4 → L4 GPU, or reduce `max_length` in tokenization |
| Drive disconnects | Add `drive.flush_and_unmount()` checkpoints |
| Missing openenv | Ensure openenv folder is synced with GitHub/Drive |

## Quick Start Template

```python
# 1. Mount drive
from google.colab import drive
drive.mount('/content/drive')

# 2. Clone or upload project
!git clone https://github.com/YOUR_USERNAME/MetaHackUI.git
%cd MetaHackUI

# 3. Install deps
!pip install -q -r requirements.txt
!pip install -q -r project/requirements.txt

# 4. Run training (see notebooks for full code)
# Python training scripts run with real-time monitoring
```

## Post-Training

1. **Download Results**: Notebooks auto-save to Drive's `/MetaHackUI/results`
2. **Load Model**: Use `transformers.AutoModel.from_pretrained("./finetuned_model")`
3. **Evaluate**: Run evaluation scripts provided in notebooks
4. **Visualize**: Open generated HTML dashboards with metrics
