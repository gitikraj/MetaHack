# 🚀 Google Colab Training Guide

## Two Notebooks for Your Pipeline

### 1️⃣ **SFT Training** (`colab_sft_training.ipynb`)
Fine-tune Qwen2.5-3B on your cybersecurity data with LoRA

**What it does:**
- Loads your `train.jsonl` dataset
- Fine-tunes Qwen2.5-3B-Instruct with LoRA adapters
- Tracks loss curves in TensorBoard
- Generates `training_metrics.png` with 4 graphs
- Saves fine-tuned model to Google Drive

**Output graphs:**
- Training loss over steps
- Learning rate schedule
- Training configuration
- Final metrics summary

**Time estimate:** 10-15 min on T4 GPU

---

### 2️⃣ **RL Training** (`colab_rl_training.ipynb`)
Train PPO policy to optimize cybersecurity detection parameters

**What it does:**
- Loads incident cases from `dataset/cases.json`
- Initializes agents (LogAgent, CodeAgent, etc.)
- Creates CyberMultiAgentEnv (Gymnasium-compatible)
- Trains PPO policy for 10,000 timesteps
- Tracks rewards and episode metrics
- Generates `training_graphs.png` with 4 graphs

**Output graphs:**
- Episode rewards over time + moving average
- Episode length distribution (histogram)
- Cumulative reward progress
- Training configuration & results

**Time estimate:** 15-20 min on T4 GPU

---

## How to Use (Step-by-Step)

### Before You Start:
```
1. Create GitHub repo with MetaHackUI code
2. Go to https://colab.research.google.com/
3. Upload notebook or: New Notebook → File → Upload
```

### For SFT Training:
```python
# In Colab:
1. Update REPO_URL in Step 1 with your GitHub URL
2. Run all cells from top to bottom
3. Cell 1-3: Setup (GPU, Drive, deps)
4. Cell 4-7: Load data and model
5. Cell 8-10: Train and generate graphs
6. Results saved to: Google Drive > MetaHackUI_results/
```

### For RL Training:
```python
# In Colab:
1. Update REPO_URL in Step 1
2. Run cells sequentially
3. Cell 1-4: Setup
4. Cell 5-7: Load cases and initialize agents
5. Cell 8-10: Train with PPO
6. Results saved to: Google Drive > MetaHackUI_RL_results/
```

---

## Generated Graphs

### SFT Training Outputs:
```
training_metrics.png contains:
├─ Top-left: Loss curve (steps vs loss)
├─ Top-right: Learning rate schedule
├─ Bottom-left: Training configuration (text)
└─ Bottom-right: Final metrics & artifacts
```

### RL Training Outputs:
```
training_graphs.png contains:
├─ Top-left: Episode rewards + moving avg
├─ Top-right: Episode length histogram
├─ Bottom-left: Cumulative reward progress
└─ Bottom-right: PPO config & results
```

---

## Troubleshooting

### "CUDA out of memory"
```python
# In notebook, modify batch size:
per_device_train_batch_size=1           # already optimized
gradient_accumulation_steps=8           # or reduce to 4
max_length=512                          # or reduce to 256
```

### "Module not found: openenv"
```bash
# Make sure repo structure has:
- agents/
- openenv/
- rl/
- dataset/
```

### "No GPU detected"
```
1. Go to Runtime → Change runtime type
2. Select T4 or L4 GPU
3. Click Save
```

### "Drive quota exceeded"
```python
# Delete old results:
!rm -rf "/content/drive/My Drive/MetaHackUI_results"
# Or upload to a different Drive
```

---

## Real-Time Monitoring During Training

### Option 1: TensorBoard (In Notebook)
Each notebook includes a TensorBoard cell that displays live metrics

### Option 2: Check Terminal Output
Both notebooks print updates every 10-100 steps showing:
- Current loss
- Episode rewards
- Training progress

### Option 3: Download Partial Results
While training is running:
1. Go to Google Drive
2. Download `.png` graphs as they're generated
3. Check `training_metrics.json` for numerical results

---

## Post-Training

### Download Your Models:
```
Google Drive > MetaHackUI_results/
├─ finetuned_model/     (Qwen2.5-3B + LoRA)
├─ training_metrics.png (SFT graphs)
└─ training_stats.json

Google Drive > MetaHackUI_RL_results/
├─ ppo_policy.zip       (Trained RL policy)
├─ training_graphs.png  (RL graphs)
└─ training_metrics.json
```

### Use Fine-tuned Model:
```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import AutoPeftModelForCausalLM

model = AutoPeftModelForCausalLM.from_pretrained("path/to/finetuned_model")
tokenizer = AutoTokenizer.from_pretrained("path/to/finetuned_model")

# Generate
inputs = tokenizer("Your prompt...", return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=256)
```

### Use Trained Policy:
```python
from stable_baselines3 import PPO
model = PPO.load("ppo_policy.zip")

# Make predictions
obs, _ = env.reset()
action, _ = model.predict(obs, deterministic=True)
```

---

## Next: Combine Both Models

After training both:

```python
# 1. Load SFT model
from peft import AutoPeftModelForCausalLM
sft_model = AutoPeftModelForCausalLM.from_pretrained("./finetuned_model")

# 2. Load RL policy
from stable_baselines3 import PPO
rl_policy = PPO.load("ppo_policy.zip")

# 3. Use together in your detection pipeline
# - SFT model analyzes logs/code
# - RL policy optimizes sensitivity parameters
```

---

## Hyperparameters You Can Tune

### SFT Training:
```python
learning_rate=2e-4          # Try: 1e-4 to 5e-4
num_train_epochs=3          # Try: 1 to 5
per_device_train_batch_size=1    # Already optimal for T4
gradient_accumulation_steps=8    # Increase for larger "batch"
max_length=512              # Reduce to 256 for speed
```

### RL Training:
```python
learning_rate=3e-4          # Try: 1e-4 to 1e-3
n_steps=2048                # Experience per update
batch_size=64               # Mini-batch size
n_epochs=10                 # Policy updates per batch
total_timesteps=10000       # Increase for better policy
```

---

## Tips for Best Results

✅ **Always use GPU** (T4 or better)  
✅ **Keep datasets under 10K examples** (for Colab limits)  
✅ **Monitor TensorBoard** (live graphs)  
✅ **Save checkpoints frequently** (both notebooks do this)  
✅ **Run on Colab Pro** (for longer training sessions)  
✅ **Check token limits** (make sure code fits)  

---

**Happy training! 🚀**
