#!/usr/bin/env python3
"""
Download and visualize training results from Google Colab.

This script helps you:
1. Download trained models from Google Drive
2. Load and visualize training metrics
3. Compare SFT vs RL training results
4. Generate comparison reports

Usage:
    python download_colab_results.py --drive-path "MetaHackUI_results"
    python download_colab_results.py --load-local "path/to/results"
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import subprocess

try:
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def download_from_drive(folder_name: str, output_path: str = "./colab_results") -> bool:
    """
    Download results from Google Drive using gdrive CLI or web interface.
    
    Args:
        folder_name: Folder name in Google Drive (e.g., "MetaHackUI_results")
        output_path: Local directory to save results
    
    Returns:
        True if successful, False otherwise
    """
    print(f"📥 Downloading from Google Drive: {folder_name}")
    print(f"   Output: {output_path}")
    print("\n⚠️  Manual Download Method (Easiest):")
    print("   1. Go to https://drive.google.com")
    print(f"   2. Find folder: {folder_name}")
    print("   3. Right-click → Download")
    print("   4. Extract to ./colab_results/")
    
    try:
        # Alternative: Use gdown if installed
        import gdown
        print("\n✅ gdown available - use for direct download")
        print(f"   gdown --folder {folder_name} -O {output_path}")
    except ImportError:
        print("\n💡 Tip: Install gdown for CLI download:")
        print("   pip install gdown")
    
    return False


def load_training_metrics(results_path: str) -> Optional[Dict]:
    """Load training metrics from local results directory."""
    metrics_file = Path(results_path) / "training_metrics.json"
    
    if not metrics_file.exists():
        print(f"❌ No training_metrics.json found in {results_path}")
        return None
    
    try:
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        print(f"✅ Loaded metrics: {list(metrics.keys())}")
        return metrics
    except Exception as e:
        print(f"❌ Error loading metrics: {e}")
        return None


def load_training_image(results_path: str, image_name: str = "training_metrics.png") -> bool:
    """Display training graph image."""
    image_path = Path(results_path) / image_name
    
    if not image_path.exists():
        print(f"❌ No {image_name} found in {results_path}")
        return False
    
    try:
        if MATPLOTLIB_AVAILABLE:
            import matplotlib.image as mpimg
            img = mpimg.imread(image_path)
            plt.figure(figsize=(16, 10))
            plt.imshow(img)
            plt.axis('off')
            plt.title(image_name)
            plt.tight_layout()
            plt.show()
            print(f"✅ Displayed: {image_name}")
        else:
            print(f"📊 Image saved at: {image_path}")
            print("   (Install matplotlib to display)")
        return True
    except Exception as e:
        print(f"❌ Error displaying image: {e}")
        return False


def display_metrics(metrics: Dict) -> None:
    """Pretty-print training metrics."""
    print("\n" + "="*60)
    print("📊 TRAINING METRICS")
    print("="*60)
    
    for key, value in metrics.items():
        if isinstance(value, dict):
            print(f"\n{key.upper()}:")
            for k, v in value.items():
                print(f"  {k}: {v}")
        else:
            print(f"{key}: {value}")
    
    print("\n" + "="*60)


def compare_results(sft_results: Optional[Dict], rl_results: Optional[Dict]) -> None:
    """Compare SFT and RL training results."""
    print("\n" + "="*60)
    print("📊 COMPARISON: SFT vs RL TRAINING")
    print("="*60)
    
    # Create comparison table
    if MATPLOTLIB_AVAILABLE:
        comparison_data = {
            'Metric': [],
            'SFT': [],
            'RL': []
        }
        
        if sft_results:
            print("\n🔵 SFT Training Results:")
            if 'final_loss' in sft_results:
                comparison_data['Metric'].append('Final Loss')
                comparison_data['SFT'].append(f"{sft_results['final_loss']:.4f}")
                comparison_data['RL'].append("-")
            
            if 'model' in sft_results:
                print(f"  Model: {sft_results['model']}")
        
        if rl_results:
            print("\n🟠 RL Training Results:")
            if 'mean_episode_reward' in rl_results:
                comparison_data['Metric'].append('Mean Reward')
                if 'final_loss' in sft_results:
                    comparison_data['SFT'].append("-")
                comparison_data['SFT'].append("-")
                comparison_data['RL'].append(f"{rl_results['mean_episode_reward']:.4f}")
            
            if 'episodes_trained' in rl_results:
                print(f"  Episodes: {rl_results['episodes_trained']}")
        
        if comparison_data['Metric']:
            df = pd.DataFrame(comparison_data)
            print("\n" + df.to_string(index=False))
    else:
        if sft_results:
            print(f"\n🔵 SFT: {sft_results}")
        if rl_results:
            print(f"\n🟠 RL: {rl_results}")
    
    print("\n" + "="*60)


def generate_summary_report(results_dir: str) -> str:
    """Generate a text summary report of training results."""
    report_lines = [
        "=" * 70,
        "COLAB TRAINING SUMMARY REPORT",
        "=" * 70,
        f"\nResults Location: {results_dir}\n"
    ]
    
    # Check for SFT results
    sft_path = Path(results_dir) / "MetaHackUI_results"
    if sft_path.exists():
        report_lines.append("🔵 SFT TRAINING")
        report_lines.append("-" * 70)
        
        metrics_file = sft_path / "training_metrics.json"
        if metrics_file.exists():
            with open(metrics_file) as f:
                metrics = json.load(f)
            report_lines.append(f"  Final Loss: {metrics.get('final_loss', 'N/A')}")
            report_lines.append(f"  Model: {metrics.get('model', 'N/A')}")
            report_lines.append(f"  Checkpoint: {metrics.get('checkpoint_path', 'N/A')}")
        
        graph_file = sft_path / "training_metrics.png"
        report_lines.append(f"  Graph: {'✅' if graph_file.exists() else '❌'} {graph_file}")
        report_lines.append("")
    
    # Check for RL results
    rl_path = Path(results_dir) / "MetaHackUI_RL_results"
    if rl_path.exists():
        report_lines.append("🟠 RL TRAINING")
        report_lines.append("-" * 70)
        
        metrics_file = rl_path / "training_metrics.json"
        if metrics_file.exists():
            with open(metrics_file) as f:
                metrics = json.load(f)
            report_lines.append(f"  Episodes: {metrics.get('episodes_trained', 'N/A')}")
            report_lines.append(f"  Mean Reward: {metrics.get('mean_episode_reward', 'N/A')}")
            report_lines.append(f"  Algorithm: {metrics.get('model_type', 'N/A')}")
        
        graph_file = rl_path / "training_graphs.png"
        report_lines.append(f"  Graph: {'✅' if graph_file.exists() else '❌'} {graph_file}")
        report_lines.append("")
    
    report_lines.append("=" * 70)
    report_lines.append("Next Steps:")
    report_lines.append("1. Review graphs: training_metrics.png / training_graphs.png")
    report_lines.append("2. Download models from Google Drive")
    report_lines.append("3. Use fine-tuned model in detection pipeline")
    report_lines.append("4. Integrate RL policy for parameter optimization")
    report_lines.append("=" * 70)
    
    report = "\n".join(report_lines)
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Download and visualize Colab training results"
    )
    parser.add_argument("--download", type=str, help="Download from Google Drive folder")
    parser.add_argument("--local-path", type=str, default="./colab_results",
                        help="Local path to results directory")
    parser.add_argument("--show-sft", action="store_true", help="Show SFT training graphs")
    parser.add_argument("--show-rl", action="store_true", help="Show RL training graphs")
    parser.add_argument("--compare", action="store_true", help="Compare SFT vs RL")
    parser.add_argument("--report", action="store_true", help="Generate summary report")
    
    args = parser.parse_args()
    
    print("\n🚀 Colab Results Downloader\n")
    
    # Download if requested
    if args.download:
        download_from_drive(args.download, args.local_path)
    
    # Load and display results
    local_path = Path(args.local_path)
    
    # Check SFT results
    sft_path = local_path / "MetaHackUI_results"
    sft_metrics = None
    if sft_path.exists():
        print(f"\n📂 Found SFT results: {sft_path}")
        sft_metrics = load_training_metrics(str(sft_path))
        if args.show_sft:
            load_training_image(str(sft_path), "training_metrics.png")
    
    # Check RL results
    rl_path = local_path / "MetaHackUI_RL_results"
    rl_metrics = None
    if rl_path.exists():
        print(f"\n📂 Found RL results: {rl_path}")
        rl_metrics = load_training_metrics(str(rl_path))
        if args.show_rl:
            load_training_image(str(rl_path), "training_graphs.png")
    
    # Display metrics
    if sft_metrics:
        display_metrics(sft_metrics)
    if rl_metrics:
        display_metrics(rl_metrics)
    
    # Compare results
    if args.compare and (sft_metrics or rl_metrics):
        compare_results(sft_metrics, rl_metrics)
    
    # Generate report
    if args.report:
        report = generate_summary_report(str(local_path))
        print(report)
        
        # Save report
        report_file = local_path / "training_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\n✅ Report saved: {report_file}")


if __name__ == "__main__":
    main()
