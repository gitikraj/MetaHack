## 📚 Complete Colab Training Setup

Created **3 complete resources** for training your model on Google Colab:

### 📓 Notebooks

#### 1. **[colab_sft_training.ipynb](colab_sft_training.ipynb)**
Fine-tune Qwen2.5-3B-Instruct on cybersecurity detection

**10 Steps:**
1. GPU setup verification
2. Mount Google Drive
3. Install all dependencies
4. Load training dataset (`train.jsonl`)
5. Load model & LoRA configuration
6. Format & tokenize data
7. Configure training arguments
8. **Train with real-time monitoring**
9. Save model to Drive
10. **Generate training graphs** + test inference

**Output:**
- Fine-tuned model saved to Drive
- `training_metrics.png` - 4 graphs (loss, LR schedule, config, results)
- TensorBoard logs for live monitoring
- Training statistics JSON

**Duration:** ~10-15 min on T4 GPU

---

#### 2. **[colab_rl_training.ipynb](colab_rl_training.ipynb)**
Train PPO policy on your custom CyberMultiAgentEnv

**10 Steps:**
1. GPU setup
2. Clone repository
3. Install dependencies
4. Load incident cases
5. Initialize all agents + evaluator
6. Create Gymnasium environment
7. Setup PPO with custom callback for metrics
8. **Train with episode reward tracking**
9. Save trained policy
10. **Generate reward curves + evaluate**

**Output:**
- Trained PPO model (`.zip` file)
- `training_graphs.png` - 4 graphs (rewards, episode lengths, cumulative, config)
- TensorBoard logs
- Training metrics JSON

**Duration:** ~15-20 min on T4 GPU

---

### 📖 Guides

#### **[COLAB_QUICKSTART.md](COLAB_QUICKSTART.md)**
Step-by-step setup guide including:
- How to use each notebook
- Real-time monitoring tips
- GPU troubleshooting
- Hyperparameter tuning guide
- How to combine both models

---

### 🛠️ Utilities

#### **[download_colab_results.py](download_colab_results.py)**
Python utility to manage results locally:

```bash
# View all results
python download_colab_results.py --local-path ./colab_results --report

# Show graphs
python download_colab_results.py --local-path ./colab_results --show-sft --show-rl

# Compare SFT vs RL
python download_colab_results.py --local-path ./colab_results --compare
```

---

## 🎯 Quick Start (5 minutes)

### Step 1: Prepare Repository
```bash
# Push to GitHub (or Colab will download from Drive)
git push origin main
```

### Step 2: Create Colab Notebooks
- Go to https://colab.research.google.com/
- Click "New notebook"
- Or upload `colab_sft_training.ipynb` / `colab_rl_training.ipynb`

### Step 3: Update GitHub URL
In both notebooks, find this line:
```python
REPO_URL = "https://github.com/YOUR_USERNAME/MetaHackUI.git"  # 👈 UPDATE
```

### Step 4: Select GPU Runtime
- Runtime → Change runtime type → GPU (T4 or L4)

### Step 5: Run!
- Run cells from top to bottom
- Monitor TensorBoard for live metrics
- Download results from Google Drive

---

## 📊 Graphs You'll Get

### From **SFT Training** (`training_metrics.png`):
```
┌─────────────────────────────────────────┐
│  Training Loss      │  Learning Rate    │
│  (steps vs loss)    │  (schedule)       │
├─────────────────────────────────────────┤
│  Config (text)      │  Results (text)   │
│  Batch size, LR,    │  Final loss,      │
│  epochs, etc        │  artifacts        │
└─────────────────────────────────────────┘
```

### From **RL Training** (`training_graphs.png`):
```
┌─────────────────────────────────────────┐
│  Episode Rewards    │  Length Histogram │
│  + Moving Avg       │  (episodes dist)  │
├─────────────────────────────────────────┤
│  Cumulative Reward  │  Config (text)    │
│  (progress)         │  & Results        │
└─────────────────────────────────────────┘
```

---

## 🗂️ Google Drive Output Structure

After training, your Drive will have:

```
Google Drive
└── MetaHackUI_results/
    ├── finetuned_model/
    │   ├── adapter_config.json
    │   ├── adapter_model.bin
    │   ├── config.json
    │   ├── special_tokens_map.json
    │   ├── tokenizer.model
    │   └── tokenizer_config.json
    ├── logs/
    │   └── events.out.tfevents.*  (TensorBoard)
    ├── training_metrics.png       (4 graphs)
    ├── training_stats.json
    └── README.md
```

And for RL:

```
Google Drive
└── MetaHackUI_RL_results/
    ├── ppo_policy.zip            (trained model)
    ├── tb_logs/
    │   └── events.out.tfevents.*
    ├── training_graphs.png       (4 graphs)
    ├── training_metrics.json
    └── README.md
```

---

## 💡 Key Features

✅ **Real-time monitoring**
- TensorBoard integrated in both notebooks
- Live loss/reward curves
- Custom callbacks for detailed tracking

✅ **Automatic checkpointing**
- Models saved to Google Drive (no local storage limits)
- Epoch-based checkpoints for SFT
- Best policy saved for RL

✅ **Optimized for Colab**
- Gradient accumulation for larger effective batches
- Memory-efficient LoRA training
- FP16 precision enabled
- Paged AdamW optimizer

✅ **Production-ready**
- Full inference testing included
- Model cards generated
- Results exportable to JSON/PNG

---

## 🚀 After Training

### Use Fine-tuned Model:
```python
from peft import AutoPeftModelForCausalLM
model = AutoPeftModelForCausalLM.from_pretrained("finetuned_model")
tokenizer = AutoTokenizer.from_pretrained("finetuned_model")

inputs = tokenizer("Detect attack in logs...", return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=256)
```

### Use RL Policy:
```python
from stable_baselines3 import PPO
policy = PPO.load("ppo_policy.zip")

obs, _ = env.reset()
action, _ = policy.predict(obs, deterministic=True)
obs, reward, done, _, _ = env.step(action)
```

### Combine Both:
```python
# SFT model analyzes security events
detection = sft_model.generate(...)

# RL policy optimizes sensitivity parameters
policy_action = rl_policy.predict(observation)

# Apply optimized parameters
adjusted_policy = apply_deltas(policy_state, policy_action)
```

---

## ⚙️ Customization

### Adjust SFT Training:
```python
# In colab_sft_training.ipynb, Step 6:
training_args = TrainingArguments(
    learning_rate=2e-4,          # ↑ increase for faster learning
    num_train_epochs=3,          # ↑ more epochs = better accuracy
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,  # ↑ simulate larger batches
    max_length=512,              # ↓ reduce for speed
)
```

### Adjust RL Training:
```python
# In colab_rl_training.ipynb, Step 6:
model = PPO(
    learning_rate=3e-4,          # Try: 1e-4 to 1e-3
    n_steps=2048,                # Experience per update
    n_epochs=10,                 # Policy optimization passes
    total_timesteps=10000,       # ↑ train longer = better policy
)
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `CUDA out of memory` | Reduce `per_device_train_batch_size` to 1, or reduce `max_length` to 256 |
| `FileNotFoundError: train.jsonl` | Ensure data is in GitHub repo or uploaded to Drive first |
| `Module not found: openenv` | Check GitHub repo has `agents/`, `openenv/`, `rl/` folders |
| `No GPU detected` | Runtime → Change runtime type → Select T4 GPU |
| `Drive quota exceeded` | Delete old results: `!rm -rf "/content/drive/My Drive/MetaHackUI_results"` |
| `TensorBoard not showing` | Wait 30 sec after training starts, refresh cell |

---

## 📞 Need Help?

Check [COLAB_QUICKSTART.md](COLAB_QUICKSTART.md) for detailed troubleshooting and tuning guides.

---

**Everything is ready! Upload the notebooks to Colab and start training. 🚀**
