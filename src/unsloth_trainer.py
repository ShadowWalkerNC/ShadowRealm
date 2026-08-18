"""
Unsloth LLM Fine-Tuning integration for ShadowRealm.
Provides CLI helpers to install, verify, and launch fine-tuning runs
via Unsloth — 2-5x faster, 70% less VRAM than vanilla HuggingFace.

GitHub: https://github.com/unslothai/unsloth
Models: Llama, Gemma, DeepSeek, Mistral, Phi (LoRA / QLoRA / DPO / GRPO)

Requirements: Python 3.10+, NVIDIA GPU (CUDA), PyTorch
"""

import os
import subprocess
import shutil
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

UNSLOTH_GITHUB = "https://github.com/unslothai/unsloth"
UNSLOTH_COLAB = "https://colab.research.google.com/github/unslothai/unsloth/blob/main/Unsloth_Studio_2025.ipynb"

SUPPORTED_MODELS = [
    "unsloth/Meta-Llama-3.1-8B",
    "unsloth/gemma-2-9b",
    "unsloth/Mistral-Nemo-Base-2407",
    "unsloth/Phi-3.5-mini-instruct",
    "unsloth/DeepSeek-R1-Distill-Llama-8B",
    "unsloth/Qwen2.5-7B",
]


def check_unsloth_status() -> Dict[str, Any]:
    """Check if Unsloth and its dependencies are available."""
    status = {
        "ok": False,
        "unsloth_installed": False,
        "torch_available": False,
        "cuda_available": False,
        "gpu_name": None,
        "vram_gb": None,
        "recommended_models": SUPPORTED_MODELS,
    }

    # Check torch + CUDA
    try:
        import torch  # type: ignore
        status["torch_available"] = True
        if torch.cuda.is_available():
            status["cuda_available"] = True
            status["gpu_name"] = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            status["vram_gb"] = round(vram, 1)
    except ImportError:
        pass

    # Check unsloth
    try:
        import unsloth  # type: ignore
        status["unsloth_installed"] = True
        status["ok"] = True
    except ImportError:
        status["unsloth_installed"] = False

    return status


def install_unsloth() -> Dict[str, Any]:
    """Install Unsloth with CUDA support via pip."""
    status = check_unsloth_status()
    if status["unsloth_installed"]:
        return {"ok": True, "status": "already_installed", **status}

    if not status["cuda_available"]:
        return {
            "ok": False,
            "error": "CUDA not available. Unsloth requires an NVIDIA GPU with CUDA drivers installed.",
            "tip": f"You can still try Unsloth on Google Colab (free T4 GPU): {UNSLOTH_COLAB}",
        }

    # Install unsloth with CUDA extras
    cmd = "pip install unsloth --quiet"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode == 0:
        return {"ok": True, "status": "installed", "message": "Unsloth installed successfully!"}
    return {"ok": False, "error": res.stderr.strip()}


def launch_unsloth_finetune(
    model: str = "unsloth/Meta-Llama-3.1-8B",
    dataset: str = "",
    output_dir: str = "./unsloth_output",
    max_steps: int = 60,
    lora_r: int = 16,
) -> Dict[str, Any]:
    """Launch a quick Unsloth fine-tuning run on a supported model.

    Args:
        model:      HuggingFace model ID (must be an unsloth/ model)
        dataset:    HuggingFace dataset ID (e.g. 'yahma/alpaca-cleaned')
        output_dir: Where to save the fine-tuned LoRA adapter
        max_steps:  Training steps (60 = ~5min on 4090, good for smoke tests)
        lora_r:     LoRA rank (8=fast/small, 64=best quality)

    Returns:
        dict with ok, message, output_dir
    """
    status = check_unsloth_status()
    if not status["unsloth_installed"]:
        return {
            "ok": False,
            "error": "Unsloth not installed. Run install_unsloth() first.",
        }
    if not dataset:
        return {"ok": False, "error": "No dataset specified. Example: 'yahma/alpaca-cleaned'"}

    script = f"""
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments
import torch

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="{model}",
    max_seq_length=2048,
    load_in_4bit=True,
)
model = FastLanguageModel.get_peft_model(
    model, r={lora_r}, target_modules=["q_proj","k_proj","v_proj","o_proj",
    "gate_proj","up_proj","down_proj"],
    lora_alpha={lora_r*2}, lora_dropout=0, bias="none", use_gradient_checkpointing="unsloth",
)
dataset = load_dataset("{dataset}", split="train")
trainer = SFTTrainer(
    model=model, tokenizer=tokenizer, train_dataset=dataset,
    dataset_text_field="text",
    args=TrainingArguments(output_dir="{output_dir}", max_steps={max_steps},
        per_device_train_batch_size=2, gradient_accumulation_steps=4,
        fp16=not torch.cuda.is_bf16_supported(), bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10, save_steps={max_steps}, report_to="none"),
)
trainer.train()
model.save_pretrained("{output_dir}/lora_model")
tokenizer.save_pretrained("{output_dir}/lora_model")
print("Fine-tuning complete! Saved to {output_dir}/lora_model")
"""
    script_path = os.path.join(output_dir, "train.py")
    os.makedirs(output_dir, exist_ok=True)
    with open(script_path, "w") as f:
        f.write(script)

    logger.info("Launching Unsloth fine-tuning: %s on %s", model, dataset)
    proc = subprocess.Popen(
        ["python", script_path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    return {
        "ok": True,
        "status": "running",
        "message": f"Fine-tuning started (PID {proc.pid}). Check {output_dir} for output.",
        "model": model,
        "dataset": dataset,
        "output_dir": output_dir,
        "max_steps": max_steps,
        "script": script_path,
        "pid": proc.pid,
    }


def get_model_recommendations(vram_gb: float) -> list:
    """Recommend models based on available VRAM."""
    if vram_gb >= 24:
        return ["unsloth/Meta-Llama-3.1-70B-bnb-4bit", "unsloth/gemma-2-27b-bnb-4bit"]
    elif vram_gb >= 12:
        return ["unsloth/Meta-Llama-3.1-8B", "unsloth/gemma-2-9b", "unsloth/Phi-3.5-mini-instruct"]
    elif vram_gb >= 6:
        return ["unsloth/Phi-3.5-mini-instruct", "unsloth/Qwen2.5-7B-bnb-4bit"]
    else:
        return ["unsloth/tinyllama-bnb-4bit"]
