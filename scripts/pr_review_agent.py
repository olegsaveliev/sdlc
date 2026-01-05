#!/usr/bin/env python3
"""
AI PR Review Agent
Reviews the actual code files in a pull request and provides feedback.
"""

import os
import sys
import git
import requests
from openai import OpenAI
from auto_tracker import track_openai  # ← ADDED: Auto-tracking import

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
#SLACK_WEBHOOK = os.environ.get('SLACK_PR_REVIEW')
SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')

# Review settings
MAX_FILE_SIZE = 5000  # Max characters per file to review
MAX_FILES = 10        # Max number of files to review
AI_MODEL = 'gpt-4o-mini'
AI_TEMPERATURE = 0.3
AI_MAX_TOKENS = 1500

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
        repo = git.Repo('.')
        
        # Get files changed compared to base branch
        repo.remotes.origin.fetch(BASE_REF)
        base_commit = repo.commit(f'origin/{BASE_REF}')
        head_commit = repo.commit('HEAD')
        
        # Get list of changed files
        changed_files = []
        diffs = base_commit.diff(head_commit)
        
        for diff in diffs:
            # Get the file path (use b_path for new/modified files)
            file_path = diff.b_path if diff.b_path else diff.a_path
            
            # Only include files that exist and are code files
            if file_path and os.path.exists(file_path):
                # Skip non-code files
                if file_path.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rb', '.php', '.c', '.cpp', '.h', '.cs')):
                    changed_files.append(file_path)
        
        if not changed_files:
            print("⚠️  No code files changed")
            return []
        
        print(f"✅ Found {len(changed_files)} changed code files:")
        for f in changed_files:
            print(f"   📄 {f}")
        
        return changed_files[:MAX_FILES]  # Limit number of files
        
    except Exception as e:
        print(f"❌ Error getting changed files: {e}")
        return []


def read_file_content(file_path):
    """Read and return file content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Truncate if too large
        if len(content) > MAX_FILE_SIZE:
            content = content[:MAX_FILE_SIZE] + f"\n\n... (truncated - file is {len(content)} chars)"
        
        return content
    except Exception as e:
        print(f"⚠️  Could not read {file_path}: {e}")
        return None


def review_code_with_ai(files_content):
    """Send code to OpenAI for review."""
    print_step(2, "AI Code Review")
    
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        client = track_openai(client)  # ← ADDED: Enable auto-tracking
        
        # Build code content string
        code_sections = []
        for file_path, content in files_content.items():
            code_sections.append(f"### File: {file_path}\n```\n{content}\n```")
        
        all_code = "\n\n".join(code_sections)
        
        prompt = f"""You are a senior software engineer with 10 years experience reviewing Python code for production systems. Review these code files and provide constructive feedback.

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

EXAMPLE GOOD REVIEW:
```
## Overall Assessment
⚠️ Needs attention

## Critical Issues (🔴)
- **File: `app.py`**
  - **Line 23:** SQL query uses string concatenation
  - **Why critical:** SQL injection vulnerability
  - **Fix:** Use parameterized query: `cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))`
```

Code to review:

{all_code}

Provide your code review:"""
        
        print(f"🤖 Analyzing {len(files_content)} files with AI...")
        
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=AI_TEMPERATURE,
            max_tokens=AI_MAX_TOKENS
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


def post_to_github(review_text, files_reviewed):
    """Post review comment on GitHub PR."""
    print_step(3, "Posting Review to GitHub")
    
    if not PR_NUMBER:
        print("⚠️  Not a pull request, skipping GitHub comment")
        return
    
    try:
        # Create file list
        files_list = "\n".join([f"- `{f}`" for f in files_reviewed])
        
        # Create comment body
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
        
        # GitHub API setup
        api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Check for existing review comment
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
            # Update existing comment
            print(f"📝 Updating existing review comment")
            update_url = f"{api_url}/issues/comments/{existing_comment['id']}"
            response = requests.patch(
                update_url,
                headers=headers,
                json={'body': comment_body}
            )
            response.raise_for_status()
            print("✅ Updated review comment")
        else:
            # Create new comment
            print("📝 Creating new review comment")
            response = requests.post(
                comments_url,
                headers=headers,
                json={'body': comment_body}
            )
            response.raise_for_status()
            print("✅ Posted review comment")
        
        print(f"🔗 View: https://github.com/{REPO_OWNER}/{REPO_NAME}/pull/{PR_NUMBER}")
        
    except Exception as e:
        print(f"❌ Error posting to GitHub: {e}")


def main():
    """Main execution flow."""
    print("\n" + "=" * 60)
    print("🤖 AI PR Review Agent - Simple Code Review")
    print("=" * 60)
    
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
    print(f"   Model: {AI_MODEL}")
    
    # Step 1: Get changed files
    changed_files = get_changed_files()
    
    if not changed_files:
        print("\n⚠️  No code files to review")
        sys.exit(0)
    
    # Step 2: Read file contents
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
    
    # Step 3: Review with AI
    review = review_code_with_ai(files_content)
    
    if not review:
        print("\n❌ Failed to generate review")
        sys.exit(1)
    
    # Step 4: Post to GitHub
    post_to_github(review, list(files_content.keys()))
    
    print("\n" + "=" * 60)
    print("✅ Code Review Complete!")
    print("=" * 60)
    print()

     # Step 5: Post to Slack
    
    #slack_webhook = os.getenv('SLACK_WEBHOOK')
    
    if slack_webhook:
        print("📨 Sending to Slack...")
        
        try:
            response = requests.post(
                slack_webhook,
                json={'text': review},
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Report sent to Slack!")
            else:
                print(f"⚠️  Slack returned: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Failed to send to Slack: {e}")
    else:
        print("ℹ️  SLACK_WEBHOOK not configured, skipping Slack notification")
        print()
        print("Generated Report:")
        print("=" * 60)
        print(review)
        print("=" * 60)
    
    print()
    print("✅ PR review complete!")


# ═══════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    main()
