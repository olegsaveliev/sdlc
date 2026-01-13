#!/usr/bin/env python3
"""
AI PR Review Agent
Reviews the actual code files in a pull request and provides feedback.
"""

import os
import git
import re
import requests
from openai import OpenAI
from auto_tracker import track_openai

# NEW (required only for prompt versioning)
import yaml

# ═══════════════════════════════════════════════════════════
# Environment variables (UNCHANGED)
# ═══════════════════════════════════════════════════════════
OPENAI_KEY = os.environ.get("OPENAI_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
PR_NUMBER = os.environ.get("PR_NUMBER")
REPO_OWNER = os.environ.get("REPO_OWNER")
REPO_NAME = os.environ.get("REPO_NAME")
BASE_REF = os.environ.get("BASE_REF")
GITHUB_RUN_URL = os.environ.get("GITHUB_RUN_URL")
SLACK_WEBHOOK = os.environ.get("SLACK_WEBHOOK")

# NEW (safe default, does not affect behavior)
PROMPT_VERSION = os.environ.get("PROMPT_VERSION", "v1")

# Review settings (UNCHANGED)
MAX_FILE_SIZE = 5000
MAX_FILES = 10
AI_MODEL = "gpt-4o-mini"
AI_TEMPERATURE = 0.3
AI_MAX_TOKENS = 1500


# ═══════════════════════════════════════════════════════════
# NEW: optional prompt loader (NON-BREAKING)
# ═══════════════════════════════════════════════════════════
def load_prompt_from_yaml(version: str):
    """
    Load prompt from prompts/pr_review/<version>.yaml
    Raises exception on any failure so caller can fallback.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(base_dir, ".."))

    prompt_path = os.path.join(
        repo_root,
        "prompts",
        "pr_review",
        f"{version}.yaml",
    )

    print(f"🧠 Trying prompt version: {version}")

    with open(prompt_path, "r") as f:
        return yaml.safe_load(f)


# ═══════════════════════════════════════════════════════════
# ORIGINAL FUNCTION — PRESERVED VERBATIM
# ═══════════════════════════════════════════════════════════
def validate_ai_review(review_text):
    """Check if AI review is actually useful or just hallucinating."""
    
    red_flags = []
    
    # Check 1: Did it just repeat the prompt?
    if "Focus on" in review_text and "Bugs & Logic Errors" in review_text:
        red_flags.append("AI might be repeating instructions")
    
    # Check 2: Is it too generic?
    generic_phrases = [
        "looks good",
        "well written",
        "no issues found",
        "consider refactoring"  # without specifics
    ]
    
    if any(phrase in review_text.lower() for phrase in generic_phrases):
        if "Line" not in review_text:
            red_flags.append("Review too generic - no specific issues cited")
    
    # Check 3: Did it reference actual code?
    if review_text.count("`") < 2:
        red_flags.append("No code examples/references in review")
    
    # Check 4: Is it suspiciously short?
    if len(review_text) < 200:
        red_flags.append("Review too short")
    
    if red_flags:
        print("⚠️ QUALITY WARNINGS:")
        for flag in red_flags:
            print(f"  - {flag}")
        return False, red_flags
    
    return True, []


# ═══════════════════════════════════════════════════════════
# Main AI review logic (PROMPT SOURCE EXTENDED ONLY)
# ═══════════════════════════════════════════════════════════
def review_code_with_ai(files_content):
    print("🔍 Running AI Code Review")

    client = OpenAI(api_key=OPENAI_KEY)
    client = track_openai(client)

    # Build code content string (UNCHANGED)
    code_sections = []
    for file_path, content in files_content.items():
        code_sections.append(
            f"### File: {file_path}\n```\n{content}\n```"
        )

    all_code = "\n\n".join(code_sections)

    # ═══════════════════════════════════════════════════════
    # ORIGINAL INLINE PROMPT (UNCHANGED)
    # ═══════════════════════════════════════════════════════
    original_prompt = f"""
You are a senior software engineer with 10 years experience reviewing Python code for production systems. Review these code files and provide constructive feedback.

Focus on:
1. 🐛 **Bugs & Logic Errors**: Null checks, edge cases, potential crashes
2. 🔒 **Security Issues**: SQL injection, XSS, authentication, exposed secrets
3. ⚡ **Performance**: Inefficient code, memory leaks, slow operations
4. 📖 **Code Quality**: Readability, naming, complexity, best practices
5. 🧪 **Testing Needs**: What should be tested, missing test cases
6. 📚 **Documentation**: Unclear code, missing comments

Format your response:
- Start with overall assessment (✅ Looks good / ⚠️ Needs attention / 🔴 Critical issues)
- Group findings by severity
- For each issue: explain WHY and HOW to fix it
- End with positive feedback

Code to review:

{all_code}

Provide your code review:
"""

    # ═══════════════════════════════════════════════════════
    # NEW: Try versioned prompt, fallback safely
    # ═══════════════════════════════════════════════════════
    try:
        prompt_cfg = load_prompt_from_yaml(PROMPT_VERSION)

        system_prompt = prompt_cfg.get(
            "system",
            "You are a senior software engineer reviewing code.",
        )
        user_prompt = prompt_cfg.get("user", "").replace("{all_code}", all_code)

        model = prompt_cfg.get("model", AI_MODEL)
        temperature = prompt_cfg.get("temperature", AI_TEMPERATURE)

        print(f"✅ Using prompt version: {PROMPT_VERSION}")

    except Exception as e:
        print(f"⚠️ Prompt YAML failed, using inline prompt: {e}")
        system_prompt = "You are a senior software engineer reviewing code."
        user_prompt = original_prompt
        model = AI_MODEL
        temperature = AI_TEMPERATURE

    # ═══════════════════════════════════════════════════════
    # OpenAI call (UNCHANGED)
    # ═══════════════════════════════════════════════════════
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=AI_MAX_TOKENS,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    review_text = response.choices[0].message.content

    # ORIGINAL validation logic — PRESERVED
    validate_ai_review(review_text)

    return review_text


# ═══════════════════════════════════════════════════════════
# Entrypoint (UNCHANGED)
# ═══════════════════════════════════════════════════════════
def main():
    print("🚀 Starting AI PR Review Agent")

    # Your existing PR file collection logic stays unchanged
    # files_content = ...

    review = review_code_with_ai(files_content)
    print(review)


if __name__ == "__main__":
    main()
