# 📋 GitHub Upload Checklist

Complete this checklist before pushing to GitHub.

## ✅ Pre-Upload Steps

### 1. Clean Up Local Files
- [ ] Remove venv/ or virtual environment folder
- [ ] Remove __pycache__/ directories
- [ ] Remove *.egg-info/ directories
- [ ] Remove .pytest_cache/ folder
- [ ] Remove .mypy_cache/ folder
- [ ] Remove build/ and dist/ folders
- [ ] Remove finetuned_model/ (will regenerate on Colab)
- [ ] Remove results/ folders
- [ ] Remove project/results/ folder
- [ ] Remove project/finetuned_model/ folder
- [ ] Remove MetaHackUI_results/ folder
- [ ] Remove MetaHackUI_RL_results/ folder

### 2. Clean Up Temporary Files
- [ ] Remove *.log files
- [ ] Remove *.tmp files
- [ ] Remove *.backup files
- [ ] Remove .DS_Store (Mac) or Thumbs.db (Windows)
- [ ] Remove *.swp or *.swo files (editor backups)

### 3. Verify No Sensitive Data
- [ ] No API keys in code files
- [ ] No passwords in configuration
- [ ] No private credentials in any file
- [ ] No .env files committed (check .gitignore)
- [ ] No private keys (.pem, .key files)
- [ ] No database credentials
- [ ] No authentication tokens

### 4. Files to Include
- [ ] ✅ `.gitignore` - Excludes unnecessary files
- [ ] ✅ `.gitattributes` - Line ending consistency
- [ ] ✅ `LICENSE` - MIT License
- [ ] ✅ `CONTRIBUTING.md` - Contribution guide
- [ ] ✅ `README.md` - Project overview
- [ ] ✅ `README_COLAB.md` - Colab guide
- [ ] ✅ `COLAB_QUICKSTART.md` - Quick start
- [ ] ✅ `colab_training_guide.md` - Training details
- [ ] ✅ `GITHUB_UPLOAD_GUIDE.md` - Upload instructions
- [ ] ✅ `setup.sh` - Linux/Mac setup
- [ ] ✅ `setup.bat` - Windows setup
- [ ] ✅ `colab_combined_training.ipynb` - Single training notebook
- [ ] ✅ `colab_sft_training.ipynb` - SFT notebook (optional)
- [ ] ✅ `colab_rl_training.ipynb` - RL notebook (optional)
- [ ] ✅ `.github/` - Issue templates, PR templates
- [ ] ✅ `.github/workflows/` - CI/CD workflows

### 5. Source Code Organization
- [ ] `agents/` folder has __init__.py
- [ ] `openenv/` folder has __init__.py
- [ ] `rl/` folder has __init__.py
- [ ] All Python files follow PEP 8 style
- [ ] All public functions have docstrings
- [ ] No hardcoded file paths (use relative paths)
- [ ] No debug print statements left in code

### 6. Dependencies
- [ ] ✅ `requirements.txt` - Core dependencies
- [ ] ✅ `project/requirements.txt` - SFT dependencies
- [ ] All versions pinned or specified
- [ ] No local/development-only packages

### 7. Documentation
- [ ] README.md has clear project description
- [ ] README includes setup instructions
- [ ] README includes quick start example
- [ ] CONTRIBUTING.md explains how to contribute
- [ ] Code comments are helpful and clear
- [ ] README includes troubleshooting section
- [ ] README includes references/citations

### 8. Data Files
- [ ] ✅ `dataset/cases.json` included (if reasonable size)
- [ ] ✅ `project/train.jsonl` included (if reasonable size)
- [ ] Large files (>100MB) are NOT included
- [ ] No duplicate or backup data files
- [ ] .gitignore excludes *.backup files

### 9. Git Verification

```bash
# Before committing, run these:

# Check what will be added
git add -n .

# Verify no venv, models, or results are included
git status

# Check file sizes
find . -type f -size +50M
# (Should be mostly notebooks and data)

# Test .gitignore is working
git check-ignore -v *
```

### 10. Pre-Push Commands

```bash
# Initialize (first time)
git init
git add .
git commit -m "Initial commit: MetaHackUI with Colab training notebooks"

# Create GitHub repo on github.com, then:
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/MetaHackUI.git
git push -u origin main
```

---

## 🎯 Repository Details

### Repository Settings (on GitHub)
- [ ] Description: "Cybersecurity incident detection using LLMs + RL"
- [ ] Visibility: Public
- [ ] Add topics: machine-learning, cybersecurity, llm, reinforcement-learning, colab
- [ ] Include README: Yes
- [ ] Include license: Yes
- [ ] Include .gitignore: Yes

### Branch Protection (Optional)
- [ ] Require pull request reviews before merging
- [ ] Require status checks to pass
- [ ] Require branches to be up to date

### CI/CD Status
- [ ] GitHub Actions workflow running successfully
- [ ] All imports passing
- [ ] No linting errors (or warnings acceptable)

---

## 📦 Expected Repository Size

### Size Check
```bash
# Check total repo size
du -sh .

# Check size by directory
du -sh */ | sort -rh | head -10

# Expected breakdown:
# - Source code: 2-5 MB
# - Notebooks: 3-5 MB
# - Data: 5-20 MB
# - Docs: 1-2 MB
# TOTAL: ~15-30 MB (should be < 100 MB for free tier)
```

### Files That Take Space
- ✅ Notebooks (.ipynb) - OK to include (3-5 MB)
- ✅ Data files (.json, .jsonl) - OK if < 50 MB
- ✅ Documentation - OK to include
- ❌ Virtual environment - MUST EXCLUDE
- ❌ Model files - MUST EXCLUDE
- ❌ Training artifacts - MUST EXCLUDE

---

## ✨ Final Checklist

- [ ] All security checks passed
- [ ] All files organized correctly
- [ ] .gitignore is comprehensive
- [ ] Documentation is complete
- [ ] No large files included
- [ ] Repository size < 100 MB
- [ ] GitHub repo created
- [ ] Ready to push!

---

## 🚀 Upload Steps

```bash
# 1. Navigate to project
cd /path/to/MetaHackUI

# 2. Verify setup (run once)
git status
git add -n .

# 3. Commit and push
git add .
git commit -m "Initial commit: MetaHackUI with SFT + RL training"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/MetaHackUI.git
git push -u origin main

# 4. Verify on GitHub
# Visit https://github.com/YOUR_USERNAME/MetaHackUI
# Check files are present
# Check GitHub Actions running (if enabled)
```

---

## ✅ Post-Upload

- [ ] Repository appears on GitHub profile
- [ ] All files visible in web interface
- [ ] README renders correctly
- [ ] GitHub Actions passed
- [ ] Issues/PR templates show up
- [ ] Share link with others!

---

## 🆘 Troubleshooting

### Issue: "Large files" error
```bash
git config --global http.postBuffer 157286400
```

### Issue: Authentication error
```bash
# Use personal access token instead of password
# GitHub → Settings → Developer settings → Personal access tokens
```

### Issue: Repo size too large
```bash
# Remove large files locally
git rm --cached large_file.bin
echo "large_file.bin" >> .gitignore
git commit -m "Remove large file"
git push
```

### Issue: Want to revert last commit
```bash
git reset --soft HEAD~1
```

---

## 📞 Need Help?

- See `.github/` for issue templates
- See `CONTRIBUTING.md` for development guidelines
- See `GITHUB_UPLOAD_GUIDE.md` for detailed instructions

---

**You're all set! Happy open-sourcing! 🎉**
