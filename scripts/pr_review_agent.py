#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
from git import Repo
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_PATH = BASE_DIR / "pr_review_prompts.json"
MODEL = "gpt-4o-mini"


def fail(msg: str):
    print(f"🔴 {msg}")
    sys.exit(0)  # NEVER fail the workflow


def load_prompt():
    if not PROMPTS_PATH.exists():
        fail(f"Prompt file not found: {PROMPTS_PATH}")

    with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    version = os.getenv("PROMPT_VERSION")
    if not version:
        fail("PROMPT_VERSION not set")

    prompts = data.get("prompts", {})
    if version not in prompts:
        fail(f"Unknown PROMPT_VERSION '{version}'")

    return prompts[version]


def get_changed_files(repo: Repo, base_sha: str, head_sha: str):
    try:
        diff = repo.git.diff(base_sha, head_sha, name_only=True)
        return [f for f in diff.splitlines() if f.strip()]
    except Exception as e:
        print(f"⚠️ Diff failed: {e}")
        return []


def read_files(files):
    blocks = []
    for f in files:
        p = BASE_DIR / f
        if p.exists() and p.is_file():
            blocks.append(f"\n===== {f} =====\n{p.read_text(errors='ignore')}")
    return "\n".join(blocks)


def main():
    for var in ["OPENAI_KEY", "BASE_SHA", "HEAD_SHA"]:
        if not os.getenv(var):
            fail(f"Missing env var: {var}")

    repo = Repo(BASE_DIR)
    files = get_changed_files(repo, os.getenv("BASE_SHA"), os.getenv("HEAD_SHA"))

    if not files:
        print("✅ Looks good — no changes to review")
        return

    code = read_files(files)
    if not code.strip():
        print("✅ Looks good — no readable files")
        return

    prompt = load_prompt()

    client = OpenAI(api_key=os.getenv("OPENAI_KEY"))
    response = client.chat.completions.create(
        model=MODEL,
        temperature=prompt.get("temperature", 0.3),
        max_tokens=prompt.get("max_tokens", 1500),
        messages=[
            {"role": "system", "content": prompt.get("system", "")},
            {"role": "user", "content": prompt["template"].format(code=code)},
        ],
    )

    print("🔍 AI Analysis")
    print(response.choices[0].message.content.strip())


if __name__ == "__main__":
    main()
