#!/usr/bin/env python3
"""
AI PR Review Agent
Analyzes pull request changes and provides automated code review feedback.
"""

import os
import sys
import git
import requests
from openai import OpenAI

# ═══════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════

OPENAI_KEY = os.environ.get('OPENAI_KEY')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
PR_NUMBER = os.environ.get('PR_NUMBER')
REPO_OWNER = os.environ.get('REPO_OWNER')
REPO_NAME = os.environ.get('REPO_NAME')
BASE_REF = os.environ.get('BASE_REF')
HEAD_REF = os.environ.get('HEAD_REF')
GITHUB_RUN_URL = os.environ.get('GITHUB_RUN_URL')

# Review settings
MAX_DIFF_LENGTH = 8000  # Max characters to send to AI
AI_MODEL = 'gpt-4'
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


def get_pr_diff():
    """Get the diff between base and head branches."""
    print_step(1, "Getting PR Changes")
    
    try:
        repo = git.Repo('.')
        
        # Fetch the base branch
        print(f"📡 Fetching base branch: {BASE_REF}")
        repo.remotes.origin.fetch(BASE_REF)
        
        # Get diff
        base_commit = repo.commit(f'origin/{BASE_REF}')
        head_commit = repo.commit('HEAD')
        
        diff = repo.git.diff(base_commit, head_commit)
        
        if not diff:
            print("⚠️  No changes detected")
            return None, {}
        
        # Get stats
        files_changed = len(repo.git.diff(base_commit, head_commit, name_only=True).split('\n'))
        lines_added = diff.count('\n+') - diff.count('\n+++')
        lines_removed = diff.count('\n-') - diff.count('\n---')
        
        stats = {
            'files_changed': files_changed,
            'lines_added': lines_added,
            'lines_removed': lines_removed
        }
        
        print(f"✅ Changes detected:")
        print(f"   Files: {files_changed}")
        print(f"   Lines added: {lines_added}")
        print(f"   Lines removed: {lines_removed}")
        
        return diff, stats
        
    except Exception as e:
        print(f"❌ Error getting diff: {e}")
        return None, {}


def review_with_ai(diff_content):
    """Send diff to OpenAI for code review."""
    print_step(2, "AI Code Review")
    
    # Truncate if too large
    if len(diff_content) > MAX_DIFF_LENGTH:
        print(f"⚠️  Diff too large ({len(diff_content)} chars), truncating to {MAX_DIFF_LENGTH}")
        diff_content = diff_content[:MAX_DIFF_LENGTH] + "\n\n... (diff truncated for review)"
    
    try:
        client = OpenAI(api_key=OPENAI_KEY)
        
        prompt = f"""You are an expert code reviewer. Review this pull request diff and provide constructive feedback.

Focus on:
1. 🐛 **Bugs & Issues**: Logic errors, potential bugs, edge cases, null checks
2. 🔒 **Security**: SQL injection, XSS, auth issues, exposed secrets, input validation
3. ⚡ **Performance**: Inefficient loops, N+1 queries, memory leaks, unnecessary operations
4. 📖 **Code Quality**: Readability, naming conventions, complexity, maintainability
5. 🧪 **Testing**: Missing tests, test coverage gaps, untested edge cases
6. 📚 **Documentation**: Missing comments, unclear logic, outdated docs

Format your response:
- Start with overall assessment (✅ Looks good / ⚠️ Needs attention / 🔴 Critical issues)
- Group issues by severity:
  - 🔴 **Critical**: Security vulnerabilities, major bugs (must fix)
  - 🟡 **Important**: Performance issues, code quality (should fix)
  - 🟢 **Suggestions**: Minor improvements, style (nice to have)
- Include file names and approximate line numbers when possible
- Be constructive and specific with actionable suggestions
- End with positive feedback on what was done well
- Keep the tone helpful and encouraging

PR Diff:
```
{diff_content}
```

Provide your code review:"""
        
        print("🤖 Sending to AI for analysis...")
        
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


def post_to_github(review_text, stats):
    """Post or update review comment on GitHub PR."""
    print_step(3, "Posting Review to GitHub")
    
    if not PR_NUMBER:
        print("⚠️  Not a pull request, skipping GitHub comment")
        return
    
    try:
        # Create comment body
        comment_body = f"""## 🤖 AI Code Review

### 📊 PR Statistics
- **Files Changed:** {stats.get('files_changed', 'N/A')}
- **Lines Added:** +{stats.get('lines_added', 'N/A')}
- **Lines Removed:** -{stats.get('lines_removed', 'N/A')}

---

### 🔍 AI Analysis

{review_text}

---

### 💡 About This Review
This automated review was generated by {AI_MODEL} to help catch potential issues early. Please use human judgment for final decisions.

**Helpful?** 👍 or 👎 to provide feedback

---
*🤖 Automated PR Review | [View workflow run]({GITHUB_RUN_URL})*"""
        
        # GitHub API setup
        api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Check if we already posted a review
        print("🔍 Checking for existing review comment...")
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
            print(f"📝 Updating existing comment (ID: {existing_comment['id']})")
            update_url = f"{api_url}/issues/comments/{existing_comment['id']}"
            response = requests.patch(
                update_url,
                headers=headers,
                json={'body': comment_body}
            )
            response.raise_for_status()
            print("✅ Updated existing AI review comment")
        else:
            # Create new comment
            print("📝 Creating new comment")
            response = requests.post(
                comments_url,
                headers=headers,
                json={'body': comment_body}
            )
            response.raise_for_status()
            print("✅ Posted new AI review comment")
        
        print(f"🔗 View at: https://github.com/{REPO_OWNER}/{REPO_NAME}/pull/{PR_NUMBER}")
        
    except Exception as e:
        print(f"❌ Error posting to GitHub: {e}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text}")


def main():
    """Main execution flow."""
    print("\n" + "=" * 60)
    print("🤖 AI PR Review Agent")
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
    print(f"   Base: {BASE_REF} → Head: {HEAD_REF}")
    print(f"   Model: {AI_MODEL}")
    
    # Step 1: Get PR diff
    diff, stats = get_pr_diff()
    
    if not diff:
        print("\n⚠️  No changes to review")
        sys.exit(0)
    
    # Step 2: Review with AI
    review = review_with_ai(diff)
    
    if not review:
        print("\n❌ Failed to generate review")
        sys.exit(1)
    
    # Step 3: Post to GitHub
    post_to_github(review, stats)
    
    print("\n" + "=" * 60)
    print("✅ AI PR Review Complete!")
    print("=" * 60)
    print()


# ═══════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    main()
