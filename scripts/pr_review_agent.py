#!/usr/bin/env python3
import os
import sys
import git
import json
import requests
from openai import OpenAI
from auto_tracker import track_openai

# ═══════════════════════════════════════════════════════════
# NEW: Load Prompt Version
# ═══════════════════════════════════════════════════════════

def load_prompt_config(version=None):
    """Load prompt configuration from JSON file."""
    
    config_path = os.path.join(os.path.dirname(__file__), '../prompts/pr_review_prompts.json')
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Use specified version or active version
        prompt_version = version or os.environ.get('PROMPT_VERSION', config['active'])
        
        if prompt_version not in config['prompts']:
            print(f"⚠️  Prompt version '{prompt_version}' not found, using '{config['active']}'")
            prompt_version = config['active']
        
        prompt_config = config['prompts'][prompt_version]
        print(f"📝 Using prompt version: {prompt_version} - {prompt_config['name']}")
        
        return prompt_config, prompt_version
        
    except FileNotFoundError:
        print("⚠️  Prompt config file not found, using default prompt")
        return None, 'default'
    except Exception as e:
        print(f"⚠️  Error loading prompt config: {e}")
        return None, 'default'

# Original configuration
OPENAI_KEY = os.environ.get('OPENAI_KEY')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
PR_NUMBER = os.environ.get('PR_NUMBER')
REPO_OWNER = os.environ.get('REPO_OWNER')
REPO_NAME = os.environ.get('REPO_NAME')
BASE_REF = os.environ.get('BASE_REF')
GITHUB_RUN_URL = os.environ.get('GITHUB_RUN_URL')
SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')

MAX_FILE_SIZE = 5000
MAX_FILES = 10

# ═══════════════════════════════════════════════════════════
# Functions (keep your existing functions)
# ═══════════════════════════════════════════════════════════

def print_step(step_num, title):
    """Print formatted step header."""
    print("\n" + "━" * 60)
    print(f"STEP {step_num}: {title}")
    print("━" * 60)

# ... keep all your existing functions (get_changed_files, read_file_content, etc.) ...

def review_code_with_ai(files_content, prompt_config=None):
    """Send code to OpenAI for review using versioned prompt."""
    print_step(2, "AI Code Review")
    
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        client = track_openai(client)
        
        # Build code content string
        code_sections = []
        for file_path, content in files_content.items():
            code_sections.append(f"### File: {file_path}\n```\n{content}\n```")
        
        all_code = "\n\n".join(code_sections)
        
        # ═══════════════════════════════════════════════════════════
        # NEW: Use versioned prompt
        # ═══════════════════════════════════════════════════════════
        
        if prompt_config:
            # Use versioned prompt from config
            system_message = prompt_config['system']
            user_prompt = prompt_config['template'].format(code=all_code)
            temperature = prompt_config['temperature']
            max_tokens = prompt_config['max_tokens']
            
            print(f"🎯 Prompt: {prompt_config['name']}")
            print(f"📊 Settings: temp={temperature}, max_tokens={max_tokens}")
        else:
            # Fallback to default prompt (your original)
            system_message = "You are a senior software engineer with 10 years experience."
            user_prompt = f"Review this code:\n\n{all_code}"
            temperature = 0.3
            max_tokens = 1500
            print("⚠️  Using default prompt")
        
        print(f"🤖 Analyzing {len(files_content)} files with AI...")
        
        # Make API call with system + user messages
        response = client.chat.completions.create(
            model=os.environ.get('AI_MODEL', 'gpt-4o-mini'),
            messages=[
                {'role': 'system', 'content': system_message},
                {'role': 'user', 'content': user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        review_text = response.choices[0].message.content
        
        print("✅ AI review completed")
        print("\n" + "=" * 60)
        print(review_text)
        print("=" * 60)
        
        return review_text
        
    except Exception as e:
        print(f"❌ Error during AI review: {e}")
        return f"⚠️ AI review failed: {e}\n\nPlease review manually."

# ... keep validate_ai_review and post_to_github functions ...

def main():
    """Main execution flow."""
    print("\n" + "=" * 60)
    print("🤖 AI PR Review Agent - Versioned Prompts")
    print("=" * 60)
    
    # Load prompt configuration
    prompt_config, prompt_version = load_prompt_config()
    
    # ... your existing validation code ...
    
    if not OPENAI_KEY or not GITHUB_TOKEN:
        print("❌ Missing required environment variables")
        sys.exit(1)
    
    print(f"\n📋 Configuration:")
    print(f"   PR: #{PR_NUMBER}")
    print(f"   Repo: {REPO_OWNER}/{REPO_NAME}")
    print(f"   Prompt Version: {prompt_version}")
    
    # Get changed files
    changed_files = get_changed_files()
    if not changed_files:
        print("\n⚠️  No code files to review")
        sys.exit(0)
    
    # Read file contents
    print_step(2, "Reading File Contents")
    files_content = {}
    for file_path in changed_files:
        print(f"📖 Reading {file_path}...")
        content = read_file_content(file_path)
        if content:
            files_content[file_path] = content
    
    if not files_content:
        print("\n⚠️  Could not read any files")
        sys.exit(0)
    
    print(f"✅ Successfully read {len(files_content)} files")
    
    # Review with AI using versioned prompt
    review = review_code_with_ai(files_content, prompt_config)
    
    if not review:
        print("\n❌ Failed to generate review")
        sys.exit(1)
    
    # Validate review quality
    print("🔍 Validating review quality...")
    is_valid, red_flags = validate_ai_review(review)
    
    if not is_valid:
        print("⚠️ AI review flagged as low quality. Adding warning banner.")
        warning_msg = f"\n\n> ⚠️ **AI Warning:** This review may be generic or incomplete.\n> **Flags:** {', '.join(red_flags)}\n> **Prompt Version:** {prompt_version}\n\n"
        review = warning_msg + review
    
    # Post to GitHub
    post_to_github(review, list(files_content.keys()))
    
    # Post to Slack (if configured)
    # ... your existing Slack code ...
    
    print("\n" + "=" * 60)
    print(f"✅ PR review complete! (Used prompt: {prompt_version})")
    print("=" * 60)

if __name__ == '__main__':
    main()
