# 🔥 Google Colab Training Complete Setup

## 📋 What's Included

I've created a **complete end-to-end** Google Colab training system for your MetaHackUI project. Here's what you get:

### 1️⃣ **Two Ready-to-Use Notebooks**
- [`colab_sft_training.ipynb`](colab_sft_training.ipynb) - Fine-tune Qwen2.5-3B with LoRA
- [`colab_rl_training.ipynb`](colab_rl_training.ipynb) - Train PPO policy with custom environment

### 2️⃣ **Comprehensive Guides**
- [`COLAB_QUICKSTART.md`](COLAB_QUICKSTART.md) - Step-by-step setup & troubleshooting
- [`colab_training_guide.md`](colab_training_guide.md) - Architecture & design decisions
- [`SETUP_COLAB_COMPLETE.md`](SETUP_COLAB_COMPLETE.md) - Full reference guide

### 3️⃣ **Utility Tools**
- [`download_colab_results.py`](download_colab_results.py) - Download & visualize results locally

---

## 🎯 Your Two Training Pipelines

### 🟦 Pipeline 1: SFT Training (Supervised Fine-Tuning)
```
train.jsonl → Qwen2.5-3B-Instruct + LoRA → Fine-tuned Model
                      ↓
              Training Metrics Dashboard
              - Loss curves
              - Learning rate schedule
              - Real-time TensorBoard
```

**Duration:** 10-15 min | **Output:** `finetuned_model/` + graphs

---

### 🟠 Pipeline 2: RL Training (Reinforcement Learning)
```
cases.json → CyberMultiAgentEnv + PPO → Trained Policy
    ↓
 Agents (Log, Code, Req, Fusion, Critic)
    ↓
  Training Reward Curves Dashboard
  - Episode rewards + moving average
  - Episode length distribution
  - Cumulative progress
```

**Duration:** 15-20 min | **Output:** `ppo_policy.zip` + graphs

---

## 🚀 Quick Start

### Before Running Notebooks:

1. **Push to GitHub** (or upload to Drive)
   ```bash
   git add .
   git commit -m "Add Colab training notebooks"
   git push origin main
   ```

2. **Open Google Colab**
   - Go to https://colab.research.google.com/
   - Upload `colab_sft_training.ipynb` and `colab_rl_training.ipynb`

3. **Set GPU Runtime**
   - Runtime → Change runtime type → GPU (select T4 or L4)

4. **Update Repository URL**
   Both notebooks have this line - update it:
   ```python
   REPO_URL = "https://github.com/YOUR_USERNAME/MetaHackUI.git"
   ```

5. **Run all cells** (top to bottom)

---

## 📊 Graphs You'll Generate

### SFT Training - 4 Subplots:
```
┌────────────────────┬────────────────────┐
│  Training Loss     │  Learning Rate     │
│  (smooth curves)   │  (warmup schedule) │
├────────────────────┼────────────────────┤
│  Configuration     │  Final Results     │
│  (batch size,      │  (loss, artifacts) │
│   LR, epochs...)   │                    │
└────────────────────┴────────────────────┘
```

### RL Training - 4 Subplots:
```
┌────────────────────┬────────────────────┐
│  Episode Rewards   │  Episode Length    │
│  + Moving Avg      │  Histogram         │
├────────────────────┼────────────────────┤
│  Cumulative Reward │  Config & Results  │
│  (progress plot)   │  (metrics summary) │
└────────────────────┴────────────────────┘
```

---

## 📥 Getting Results from Colab

### Option 1: Google Drive (Automatic)
Models automatically save to:
- `Google Drive > MetaHackUI_results/` (SFT)
- `Google Drive > MetaHackUI_RL_results/` (RL)

### Option 2: Download Locally
```bash
python download_colab_results.py \
  --local-path ./colab_results \
  --show-sft \
  --show-rl \
  --compare \
  --report
```

---

## 🎓 What Each Notebook Does

### **colab_sft_training.ipynb** (10 steps)
```python
✅ Step 0:  GPU setup & verification
✅ Step 1:  Mount Drive & clone repo
✅ Step 2:  Install transformers, peft, bitsandbytes, etc.
✅ Step 3:  Load train.jsonl dataset
✅ Step 4:  Load Qwen2.5-3B + configure LoRA
✅ Step 5:  Format examples & tokenize (max_length=512)
✅ Step 6:  Setup TrainingArguments + Trainer
✅ Step 7:  Train with real-time loss monitoring
✅ Step 8:  Save model to Google Drive
✅ Step 9:  Generate training_metrics.png (4 graphs)
✅ Step 10: Test inference + TensorBoard
```

**Result:** Fine-tuned model ready for cybersecurity detection

---

### **colab_rl_training.ipynb** (10 steps)
```python
✅ Step 0:  GPU setup
✅ Step 1:  Mount Drive & clone repo
✅ Step 2:  Install gymnasium, stable-baselines3, etc.
✅ Step 3:  Load cases.json dataset
✅ Step 4:  Initialize all agents (Log, Code, Req, Fusion, Critic)
✅ Step 5:  Create CyberMultiAgentEnv (Gymnasium compatible)
✅ Step 6:  Setup PPO with custom MetricsCallback
✅ Step 7:  Train for 10,000 timesteps with reward tracking
✅ Step 8:  Save trained policy to Drive
✅ Step 9:  Generate training_graphs.png (4 graphs)
✅ Step 10: Evaluate trained policy + TensorBoard
```

**Result:** Optimized policy for adjusting detection sensitivity parameters

---

## 💾 Files Generated in Google Drive

### After SFT Training:
```
MetaHackUI_results/
├── finetuned_model/              # Complete model directory
│   ├── adapter_config.json       # LoRA config
│   ├── adapter_model.bin         # LoRA weights
│   ├── config.json               # Model config
│   ├── tokenizer.model           # Tokenizer weights
│   └── tokenizer_config.json
├── training_metrics.png          # 4 graphs (loss, LR, config, results)
├── training_stats.json           # Metrics in JSON format
└── logs/                          # TensorBoard logs
    └── events.out.tfevents.*
```

### After RL Training:
```
MetaHackUI_RL_results/
├── ppo_policy.zip                # Complete trained policy
├── training_graphs.png           # 4 graphs (rewards, lengths, cumulative, config)
├── training_metrics.json         # Metrics in JSON format
└── tb_logs/                       # TensorBoard logs
    └── events.out.tfevents.*
```

---

## 🔌 Integration with Your Pipeline

### Use Fine-tuned Model:
```python
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer

# Load from Drive
model = AutoPeftModelForCausalLM.from_pretrained("./finetuned_model")
tokenizer = AutoTokenizer.from_pretrained("./finetuned_model")

# Analyze security incident
prompt = """Logs: [...]
Requirements: [...]
Code: [...]
Analyze for attacks:"""

inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=256)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
```

### Use Trained Policy:
```python
from stable_baselines3 import PPO
from openenv import CyberMultiAgentEnv

# Load trained model
policy = PPO.load("ppo_policy.zip", env=env)

# Get optimized actions
obs, _ = env.reset()
action, _ = policy.predict(obs, deterministic=True)  # [delta_log_sens, delta_code_sens, ...]

# Apply to policy state
new_policy = PolicyState(
    log_sensitivity=current.log_sensitivity + action[0],
    code_sensitivity=current.code_sensitivity + action[1],
    # ... etc
)
```

---

## ⚙️ Performance & Tuning

### SFT Training (GPU Memory):
- **Model:** Qwen2.5-3B = ~7GB base
- **With LoRA:** ~9-10GB effective
- **Training:** Per batch 1 + 8 accumulation = batch size 8
- **Estimated time (T4):** ~10-15 minutes for 3 epochs

### RL Training (GPU Memory):
- **PPO model:** Small (~200MB)
- **Environment:** In-memory (~100-500MB)
- **Training:** 10,000 timesteps = ~300-500 episodes
- **Estimated time (T4):** ~15-20 minutes

### Tuning Hyperparameters:
```python
# More aggressive training (faster convergence):
learning_rate = 5e-4          # Higher learning rate
num_train_epochs = 5          # More epochs
gradient_accumulation_steps = 4  # Smaller accumulation

# More conservative training (better results):
learning_rate = 1e-4          # Lower learning rate
num_train_epochs = 1          # Fewer epochs
gradient_accumulation_steps = 16  # Larger accumulation
```

---

## ❓ FAQ

**Q: Can I train longer without hitting Colab timeout?**
A: Yes, Colab Pro gives 24-hour sessions. Reduce `total_timesteps` on free tier (currently 10K).

**Q: How do I combine both models?**
A: Both operate independently. Use SFT for detection, RL for parameter optimization.

**Q: Can I download partial results while training?**
A: Yes, check Google Drive periodically - `.png` files update as training progresses.

**Q: What if training gets interrupted?**
A: Models auto-save to Drive. Can resume from last checkpoint (need to modify notebook).

**Q: How do I compare results across runs?**
A: Use `download_colab_results.py --compare` to visualize metrics side-by-side.

---

## 📞 Support

For detailed guidance, see:
- [`COLAB_QUICKSTART.md`](COLAB_QUICKSTART.md) - Setup guide
- [`colab_training_guide.md`](colab_training_guide.md) - Technical details
- Notebooks themselves have detailed comments in each cell

---

## ✅ Checklist Before Running

- [ ] GitHub repo is public or credentials are set up
- [ ] `train.jsonl` exists in `project/` folder
- [ ] `cases.json` exists in `dataset/` folder  
- [ ] `agents/`, `openenv/`, `rl/` folders are in repo
- [ ] GPU runtime selected in Colab (T4 or L4)
- [ ] `REPO_URL` updated in both notebooks

---

**Ready to train? Start with the notebooks in Google Colab! 🚀**
