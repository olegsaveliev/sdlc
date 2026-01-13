import os
import sys
import yaml
import requests
from openai import OpenAI

from auto_tracker import track_openai
from github_utils import (
    get_pr_files,
    post_pr_comment,
)
from utils import print_step

# ============================================================
# 🔍 DEBUG CONTEXT (NEW – logging only, no logic change)
# ============================================================
print("📂 CWD:", os.getcwd())
print("📂 Script location:", os.path.abspath(__file__))

# ============================================================
# ENV VARS (unchanged)
# ============================================================
OPENAI_KEY = os.getenv("OPENAI_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")
PR_NUMBER = os.getenv("PR_NUMBER")

# NEW: prompt version (safe default)
PROMPT_VERSION = os.getenv("PROMPT_VERSION", "v1")

# ============================================================
# PROMPT LOADER (NEW – isolated, no logic impact)
# ============================================================
def load_prompt(agent_name: str, version: str):
    """
    Loads a versioned prompt YAML file.
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    REPO_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

    prompt_path = os.path.join(
        REPO_ROOT,
        "prompts",
        agent_name.lower(),
        f"{version}.yaml"
    )

    print(f"🧠 Loading prompt: {prompt_path}")

    if not os.path.exists(prompt_path):
        raise FileNotFoundError(
            f"❌ Prompt file not found: {prompt_path}. "
            f"Did you commit the prompts directory?"
        )

    with open(prompt_path, "r") as f:
        return yaml.safe_load(f)

# ============================================================
# CORE LOGIC (UNCHANGED – ONLY LOGGING ADDED)
# ============================================================
def review_code_with_ai(files_content):
    """Send code to OpenAI for review."""
    print_step(2, "AI Code Review")

    try:
        client = OpenAI(api_key=OPENAI_KEY)
        client = track_openai(client)

        # ----------------------------------------------------
        # Build code content string (UNCHANGED)
        # ----------------------------------------------------
        code_sections = []
        for file_path, content in files_content.items():
            code_sections.append(
                f"### File: {file_path}\n```\n{content}\n```"
            )

        all_code = "\n\n".join(code_sections)
        print(f"📦 Code payload size: {len(all_code)} characters")

        # ----------------------------------------------------
        # PROMPT START (NEW – wiring only)
        # ----------------------------------------------------
        print(f"🧠 Prompt Version: {PROMPT_VERSION}")

        prompt_config = load_prompt("pr_review", PROMPT_VERSION)

        print("📄 Prompt keys:", list(prompt_config.keys()))

        if "system" not in prompt_config or "user" not in prompt_config:
            raise ValueError(
                f"❌ Prompt '{PROMPT_VERSION}' missing 'system' or 'user' section"
            )

        system_prompt = prompt_config["system"]

        if "{all_code}" in prompt_config["user"]:
            print("🔁 Injecting code into prompt")
            user_prompt = prompt_config["user"].replace("{all_code}", all_code)
        else:
            print("⚠️ WARNING: {all_code} placeholder not found in prompt")
            user_prompt = prompt_config["user"]

        model = prompt_config.get("model", "gpt-4o-mini")
        temperature = prompt_config.get("temperature", 0.2)

        print(f"🤖 Model: {model}")
        print(f"🌡️ Temperature: {temperature}")
        # ----------------------------------------------------
        # PROMPT END
        # ----------------------------------------------------

        # ----------------------------------------------------
        # 🔽 EXISTING OPENAI CALL LOGIC (UNCHANGED)
        # ----------------------------------------------------
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        return response.choices[0].message.content

    except Exception as e:
        print("❌ AI review failed")
        print(f"❌ {type(e).__name__}: {e}")
        raise

# ============================================================
# ENTRYPOINT (UNCHANGED – logging only)
# ============================================================
def main():
    try:
        files_content = get_pr_files(
            GITHUB_TOKEN,
            REPO_OWNER,
            REPO_NAME,
            PR_NUMBER,
        )

        ai_review = review_code_with_ai(files_content)

        post_pr_comment(
            GITHUB_TOKEN,
            REPO_OWNER,
            REPO_NAME,
            PR_NUMBER,
            ai_review,
        )

    except Exception as e:
        print("❌ Fatal error in PR review agent")
        print(f"❌ {type(e).__name__}: {e}")
        raise

if __name__ == "__main__":
    main()
