#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
from typing import Dict, List

import requests
from git import Repo
from openai import OpenAI


# ───────────────────────────────────────────────────────────────
# Paths & Constants
# ───────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_PATH = BASE_DIR / "pr_review_prompts.json"

OPENAI_MODEL = "gpt-4o-mini"


# ───────────────────────────────────────────────────────────────
# Utilities
# ───────────────────────────────────────────────────────────────

def fail(message: str) -> None:
    print(f"🔴 Agent failed: {message}")
    sys.exit(1)


def load_prompt_config() -> Dict:
    if not PROMPTS_PATH.exists():
        fail(f"Prompt config not found at {PROMPTS_PATH}")

    try:
        with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        fail(f"Failed to load prompt config: {e}")


def get_prompt(prompt_config: Dict) -> Dict:
    prompt_version = os.getenv("PROMPT_VERSION")
    if not prompt_version:
        fail("PROMPT_VERSION env var is not set")

    prompts = prompt_config.get("prompts", {})
    if prompt_version not in prompts:
        fail(
            f"Prompt version '{prompt_version}' not found. "
            f"Available versions: {', '.join(prompts.keys())}"
        )

    return prompts[prompt_version]


def get_changed_files(repo: Repo, base_ref: str, head_ref: str) -> List[str]:
    diff = repo.git.diff(f"{base_ref}...{head_ref}", name_only=True)
    return [f for f in diff.splitlines() if f.strip()]


def load_files_content(files: List[str]) -> str:
    content_blocks = []

    for file_path in files:
        path = BASE_DIR / file_path
        if not path.exists() or path.is_dir():
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        content_blocks.append(
            f"\n===== FILE: {file_path} =====\n{content}\n"
        )

    return "\n".join(content_blocks)


# ───────────────────────────────────────────────────────────────
# OpenAI Review
# ───────────────────────────────────────────────────────────────

def run_review() -> None:
    # Required env vars
    required_envs = [
        "OPENAI_KEY",
        "REPO_OWNER",
        "REPO_NAME",
        "BASE_REF",
        "HEAD_REF",
    ]

    for env in required_envs:
        if not os.getenv(env):
            fail(f"Missing required env var: {env}")

    client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

    repo = Repo(BASE_DIR)

    changed_files = get_changed_files(
        repo,
        os.getenv("BASE_REF"),
        os.getenv("HEAD_REF"),
    )

    if not changed_files:
        print("⚠️ No code changes detected. Nothing to review.")
        print("✅ Looks good")
        return

    files_content = load_files_content(changed_files)

    if not files_content.strip():
        print("⚠️ No readable source files found.")
        print("✅ Looks good")
        return

    prompt_config = load_prompt_config()
    prompt = get_prompt(prompt_config)

    system_prompt = prompt.get("system", "")
    template = prompt.get("template", "")
    temperature = prompt.get("temperature", 0.3)
    max_tokens = prompt.get("max_tokens", 1500)

    user_prompt = template.format(code=files_content)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    review_text = response.choices[0].message.content.strip()

    print("🔍 AI Analysis")
    print(review_text)


# ───────────────────────────────────────────────────────────────
# Entrypoint
# ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        run_review()
    except Exception as e:
        fail(str(e))

    sys.exit(0)
