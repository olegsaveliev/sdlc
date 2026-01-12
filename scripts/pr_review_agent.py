#!/usr/bin/env python3
"""
AI PR Review Agent with Prompt Versioning
Reviews the actual code files in a pull request and provides feedback.
"""

import os
import sys
import git
import json
import requests
from openai import OpenAI
from auto_tracker import track_openai

# ═══════════════════════════════════════════════════════════
# CRITICAL: Wrap ALL imports in try/except to see what fails
# ═══════════════════════════════════════════════════════════

print("=" * 60)
print("🔍 LOADING MODULES...")
print("=" * 60)

try:
    print("Loading git...")
    import git
    print("✅ git loaded")
except ImportError as e:
    print(f"❌ Failed to import git: {e}")
    print("Installing gitpython...")
    os.system("pip install gitpython")
    import git
    print("✅ git loaded after install")

try:
    print("Loading openai...")
    from openai import OpenAI
    print("✅ openai loaded")
except ImportError as e:
    print(f"❌ Failed to import openai: {e}")
    sys.exit(1)

try:
    print("Loading auto_tracker...")
    from auto_tracker import track_openai
    print("✅ auto_tracker loaded")
except ImportError as e:
    print(f"⚠️ auto_tracker not found: {e}")
    print("⚠️ Defining dummy tracker...")
    def track_openai(client):
        print("⚠️ Using dummy tracker (auto_tracker.py not found)")
        return client

print("=" * 60)
print("✅ ALL MODULES LOADED SUCCESSFULLY")
print("=" * 60)

# ═══════════════════════════════════════════════════════════
# Load Prompt Version
# ═══════════════════════════════════════════════════════════

def load_prompt_config(version=None):
    """Load prompt configuration from JSON file."""
    
    # Try multiple possible paths
    possible_paths = [
        'prompts/pr_review_prompts.json',
        '../prompts/pr_review_prompts.json',
        os.path.join(os.path.dirname(__file__), '../prompts/pr_review_prompts.json'),
    ]
    
    print("\n🔍 Searching for prompt config...")
    for path in possible_paths:
        abs_path = os.path.abspath(path)
        print(f"   Checking: {abs_path}")
        if os.path.exists(path):
            config_path = path
            print(f"   ✅ FOUND: {abs_path}")
            break
    else:
        print("   ⚠️  Not found in any location")
        print("   📁 Current working directory:", os.getcwd())
        print("   📁 Script directory:", os.path.dirname(os.path.abspath(__file__)))
        print("   ⚠️  Will use built-in default prompt")
        return None, 'default'
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        prompt_version = version or os.environ.get('PROMPT_VERSION', config.get('active', 'default'))
        
        if prompt_version not in config.get('prompts', {}):
            print(f"⚠️  Version '{prompt_version}' not in config")
            prompt_version = config.get('active', 'default')
        
        if prompt_version == 'default' or prompt_version not in config.get('prompts', {}):
            print("⚠️  Using built-in default (version not valid)")
            return None, 'default'
        
        prompt_config = config['prompts'][prompt_version]
        print(f"✅ Loaded: {prompt_version} - {prompt_config['name']}")
        
        return prompt_config, prompt_version
        
    except Exception as e:
        print(f"⚠️  Error loading config: {e}")
        import traceback
        traceback.print_exc()
        return None, 'default'

# ═══════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════

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
# Functions
# ═══════════════════════════════════════════════════════════

def print_step(step_num, title):
    """Print formatted step header."""
    print("\n" + "━" * 60)
    print(f"STEP {step_num}: {title}")
    print("━" * 60)


def get_changed_files():
    """Get list of files that changed in this PR."""
    print_step(1, "Finding Changed Files")
    
    try:
        print("🔍 Initializing git repo...")
        repo = git.Repo('.')
        print("✅ Git repo initialized")
        
        print(f"🔍 Fetching base branch: {BASE_REF}")
        repo.remotes.origin.fetch(BASE_REF)
        print("✅ Base branch fetched")
        
        base_commit = repo.commit(f'origin/{BASE_REF}')
        head_commit = repo.commit('HEAD')
        print(f"✅ Comparing: {base_commit.hexsha[:7]} → {head_commit.hexsha[:7]}")
        
        changed_files = []
        diffs = base_commit.diff(head_commit)
        print(f"✅ Found {len(diffs)} diff entries")
        
        for diff in diffs:
            file_path = diff.b_path if diff.b_path else diff.a_path
            
            if file_path and os.path.exists(file_path):
                if file_path.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rb', '.php', '.c', '.cpp', '.h', '.cs')):
                    changed_files.append(file_path)
                    print(f"   📄 {file_path}")
        
        if not changed_files:
            print("⚠️  No code files changed (might be only docs/config)")
            return []
        
        print(f"✅ Found {len(changed_files)} code files to review")
        return changed_files[:MAX_FILES]
        
    except Exception as e:
        print(f"❌ Error getting changed files: {e}")
        import traceback
        traceback.print_exc()
        return []


def read_file_content(file_path):
    """Read and return file content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if len(content) > MAX_FILE_SIZE:
            content = content[:MAX_FILE_SIZE] + f"\n\n... (truncated - file is {len(content)} chars)"
        
        return content
    except Exception as e:
        print(f"⚠️  Could not read {file_path}: {e}")
        return None


def review_code_with_ai(files_content, prompt_config=None):
    """Send code to OpenAI for review using versioned prompt."""
    print_step(2, "AI Code Review")
    
    try:
        print("🔌 Connecting to OpenAI API...")
        client = OpenAI(api_key=OPENAI_KEY)
        client = track_openai(client)
        print("✅ Connected and tracking enabled")
        
        # Build code content string
        code_sections = []
        for file_path, content in files_content.items():
            code_sections.append(f"### File: {file_path}\n```\n{content}\n```")
        
        all_code = "\n\n".join(code_sections)
        
        if prompt_config:
            system_message = prompt_config['system']
            user_prompt = prompt_config['template'].format(code=all_code)
            temperature = prompt_config['temperature']
            max_tokens = prompt_config['max_tokens']
            
            print(f"🎯 Prompt: {prompt_config['name']}")
            print(f"📊 Settings: temp={temperature}, max_tokens={max_tokens}")
        else:
            print("⚠️  Using built-in default prompt")
            system_message = "You are a senior software engineer with 10 years experience reviewing Python code for production systems."
            
            user_prompt = f"""Review these code files and provide constructive feedback.

Focus on:
1. 🐛 **Bugs & Logic Errors**: Null checks, edge cases, potential crashes
2. 🔒 **Security Issues**: SQL injection, XSS, authentication, exposed secrets
3. ⚡ **Performance**: Inefficient code, memory leaks, slow operations
4. 📖 **Code Quality**: Readability, naming, complexity, best practices
5. 🧪 **Testing Needs**: What should be tested, missing test cases
6. 📚 **Documentation**: Unclear code, missing comments

Format your response:
- Start with overall assessment (✅ Looks good / ⚠️ Needs attention / 🔴 Critical issues)
- Group findings by severity:
  - 🔴 **Critical**: Must fix immediately (security, major bugs)
  - 🟡 **Important**: Should fix (performance, quality issues)
  - 🟢 **Suggestions**: Nice to have (style, minor improvements)
- For each issue:
  - Mention the file name
  - Point out the specific problem
  - Explain WHY it's an issue
  - Suggest HOW to fix it with code example if helpful
- End with positive feedback on what's done well
- Be helpful and constructive, not just critical

Code to review:

{all_code}

Provide your code review:"""
            
            temperature = 0.3
            max_tokens = 1500
        
        print(f"🤖 Analyzing {len(files_content)} files...")
        print(f"📊 Input size: ~{len(all_code)} characters")
        
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
        print(f"📊 Output size: ~{len(review_text)} characters")
        print("\n" + "=" * 60)
        print(review_text)
        print("=" * 60)
        
        return review_text
        
    except Exception as e:
        print(f"❌ Error during AI review: {e}")
        import traceback
        traceback.print_exc()
        # Return a basic error message but DON'T exit - continue execution
        return f"⚠️ AI review encountered an error: {str(e)}\n\nPlease review manually."


def validate_ai_review(review_text):
    """Check if AI review is actually useful or just hallucinating."""
    
    red_flags = []
    
    if "Focus on" in review_text and "Bugs & Logic Errors" in review_text:
        red_flags.append("AI might be repeating instructions")
    
    generic_phrases = ["looks good", "well written", "no issues found", "consider refactoring"]
    if any(phrase in review_text.lower() for phrase in generic_phrases):
        if "Line" not in review_text:
            red_flags.append("Review too generic - no specific issues cited")
    
    if review_text.count('`') < 2:
        red_flags.append("No code examples/references in review")
    
    if len(review_text) < 200:
        red_flags.append("Review too short")
    
    if red_flags:
        print("⚠️ QUALITY WARNINGS:")
        for flag in red_flags:
            print(f"  - {flag}")
        return False, red_flags
    
    return True, []


def post_to_github(review_text, files_reviewed):
    """Post review comment on GitHub PR."""
    print_step(3, "Posting Review to GitHub")
    
    if not PR_NUMBER:
        print("⚠️  Not a pull request, skipping GitHub comment")
        return
    
    try:
        files_list = "\n".join([f"- `{f}`" for f in files_reviewed])
        
        comment_body = f"""## 🤖 AI Code Review

### 📊 Files Reviewed
{files_list}

**Total files:** {len(files_reviewed)}

---

### 🔍 AI Analysis

{review_text}

---

### 💡 About This Review
This review analyzed the actual code in your changed files (not just the diff). The AI checked for bugs, security issues, performance problems, and code quality.

**Helpful?** React with 👍 or 👎

---
*🤖 Automated by AI PR Review Agent | [View workflow]({GITHUB_RUN_URL})*"""
        
        api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        print("🔍 Checking for existing review...")
        comments_url = f"{api_url}/issues/{PR_NUMBER}/comments"
        response = requests.get(comments_url, headers=headers)
        response.raise_for_status()
        
        existing_comment = None
        for comment in response.json():
            if '🤖 AI Code Review' in comment.get('body', ''):
                existing_comment = comment
                break
        
        if existing_comment:
            print(f"📝 Updating existing review comment")
            update_url = f"{api_url}/issues/comments/{existing_comment['id']}"
            response = requests.patch(update_url, headers=headers, json={'body': comment_body})
            response.raise_for_status()
            print("✅ Updated review comment")
        else:
            print("📝 Creating new review comment")
            response = requests.post(comments_url, headers=headers, json={'body': comment_body})
            response.raise_for_status()
            print("✅ Posted review comment")
        
        print(f"🔗 View: https://github.com/{REPO_OWNER}/{REPO_NAME}/pull/{PR_NUMBER}")
        
    except Exception as e:
        print(f"❌ Error posting to GitHub: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main execution flow with BULLETPROOF error handling."""
    print("\n" + "=" * 60)
    print("🤖 AI PR Review Agent - Versioned Prompts")
    print("=" * 60)
    
    # Exit code tracker
    exit_code = 0
    
    try:
        # Load prompt configuration
        try:
            prompt_config, prompt_version = load_prompt_config()
        except Exception as e:
            print(f"⚠️  Error loading prompt: {e}")
            import traceback
            traceback.print_exc()
            prompt_config, prompt_version = None, 'default'
        
        # Validate environment
        if not OPENAI_KEY:
            print("❌ Error: OPENAI_KEY not set")
            sys.exit(1)
        
        if not GITHUB_TOKEN:
            print("❌ Error: GITHUB_TOKEN not set")
            sys.exit(1)
        
        print(f"\n📋 Configuration:")
        print(f"   PR: #{PR_NUMBER}")
        print(f"   Repo: {REPO_OWNER}/{REPO_NAME}")
        print(f"   Prompt Version: {prompt_version}")
        
        # Get changed files
        changed_files = get_changed_files()
        
        if not changed_files:
            print("\n⚠️  No code files to review (might be docs/config only)")
            print("✅ Exiting gracefully with success code")
            sys.exit(0)  # Success - nothing to review is OK
        
        # Read file contents
        print_step(2, "Reading File Contents")
        files_content = {}
        
        for file_path in changed_files:
            print(f"📖 Reading {file_path}...")
            content = read_file_content(file_path)
            if content:
                files_content[file_path] = content
        
        if not files_content:
            print("\n⚠️  Could not read any files (permissions?)")
            print("✅ Exiting gracefully with success code")
            sys.exit(0)  # Success - nothing readable is OK
        
        print(f"✅ Successfully read {len(files_content)} files")
        
        # Review with AI
        review = review_code_with_ai(files_content, prompt_config)
        
        # Even if review has error message, continue (don't fail the workflow)
        if not review or "AI review encountered an error" in review:
            print("\n⚠️  Review failed or returned error")
            # But we still post what we have
        
        # Validate review quality
        print("🔍 Validating review quality...")
        is_valid, red_flags = validate_ai_review(review)
        
        if not is_valid:
            print("⚠️ AI review flagged as low quality. Adding warning banner.")
            warning_msg = f"\n\n> ⚠️ **AI Warning:** This review may be generic or incomplete.\n> **Flags:** {', '.join(red_flags)}\n> **Prompt Version:** {prompt_version}\n\n"
            review = warning_msg + review
        
        # Post to GitHub
        post_to_github(review, list(files_content.keys()))
        
        # Post to Slack
        if SLACK_WEBHOOK:
            print("📨 Sending to Slack...")
            try:
                slack_text = f"🤖 *AI PR Review Complete* for PR #{PR_NUMBER}\n\n"
                if not is_valid:
                    slack_text += f"⚠️ *Quality Warning:* {', '.join(red_flags)}\n\n"
                
                slack_text += review[:500] + "..." if len(review) > 500 else review
                
                response = requests.post(SLACK_WEBHOOK, json={'text': slack_text}, timeout=10)
                
                if response.status_code == 200:
                    print("✅ Report sent to Slack!")
                else:
                    print(f"⚠️  Slack returned: {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️  Failed to send to Slack: {e}")
        else:
            print("ℹ️  SLACK_WEBHOOK not configured, skipping Slack notification")
        
        print("\n" + "=" * 60)
        print(f"✅ PR review complete! (Used prompt: {prompt_version})")
        print("=" * 60)
    
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ FATAL ERROR IN MAIN:")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        print("\n⚠️  Workflow will fail but error is logged above")
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
