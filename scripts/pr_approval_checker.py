#!/usr/bin/env python3
"""
PR Approval Checker
Implements the 'Validation Pattern': Checks metrics and AI feedback to decide on auto-approval.
"""

import os
import sys
import git
import requests
import json

# Configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
PR_NUMBER = os.environ.get('PR_NUMBER')
REPO_OWNER = os.environ.get('REPO_OWNER')
REPO_NAME = os.environ.get('REPO_NAME')
BASE_REF = os.environ.get('BASE_REF')

def get_changed_files():
    """Get list of changed files using Git."""
    try:
        repo = git.Repo('.')
        repo.remotes.origin.fetch(BASE_REF)
        base = repo.commit(f'origin/{BASE_REF}')
        head = repo.commit('HEAD')
        
        diffs = base.diff(head)
        files = []
        for d in diffs:
            if d.b_path: files.append(d.b_path)
            elif d.a_path: files.append(d.a_path)
        return files
    except Exception as e:
        print(f"⚠️ Error reading git diff: {e}")
        return []

def get_ai_review_status():
    """Fetch the last AI review comment to see if it passed."""
    if not PR_NUMBER: return "unknown"
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{PR_NUMBER}/comments"
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        comments = resp.json()
        
        # Look for the last comment from our bot
        for comment in reversed(comments):
            if "🤖 AI Code Review" in comment.get('body', ''):
                return comment['body']
        return ""
    except Exception as e:
        print(f"⚠️ Error fetching comments: {e}")
        return ""

def post_comment(message):
    """Post the decision to GitHub."""
    if not PR_NUMBER: return
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{PR_NUMBER}/comments"
    requests.post(url, headers={'Authorization': f'token {GITHUB_TOKEN}'}, json={'body': message})

def assign_reviewer(user):
    """Assign a human reviewer."""
    if not PR_NUMBER: return
    print(f"👤 Assigning {user} for manual review...")
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{PR_NUMBER}/assignees"
    requests.post(url, headers={'Authorization': f'token {GITHUB_TOKEN}'}, json={'assignees': [user]})

def check_if_auto_approvable(pr_data):
    """Determine if PR can be auto-merged or needs human review."""
    print("\n🔍 Evaluating Approval Criteria...")
    
    # 1. Logic Checks
    criteria = {
        "small_change": len(pr_data["changed_files"]) <= 3,
        "low_risk_files": all(
            f.endswith(('.md', '.txt', '.yml', '.json', 'test_', '.png')) 
            for f in pr_data["changed_files"]
        ),
        "ai_review_passed": "✅" in pr_data["ai_review"], # Checks for green checkmark in AI comment
        "tests_passed": pr_data["test_status"] == "passed",
        "no_security_changes": not any(
            term in f for f in pr_data["changed_files"] for term in ["auth", "password", "secret", "login", "token"]
        )
    }

    # Print status of each check
    for key, passed in criteria.items():
        icon = "✅" if passed else "❌"
        print(f"  {icon} {key}")

    # Decision
    if all(criteria.values()):
        return {
            "auto_approve": True,
            "reason": "🚀 Low-risk change, all checks passed. Auto-approving."
        }
    else:
        failed = [k for k, v in criteria.items() if not v]
        return {
            "auto_approve": False,
            "reason": f"huma review required. Failed checks: {', '.join(failed)}",
            "assign_to": "olegsaveliev" # Hardcoded for exercise, usually would be a team
        }

def main():
    print("🤖 PR Approval Checker Started")
    
    # Gather Data
    changed_files = get_changed_files()
    ai_review_text = get_ai_review_status()
    
    # Mock test status for this exercise (in real life, fetch from GitHub Checks API)
    test_status = os.environ.get('TEST_STATUS', 'passed') 

    pr_data = {
        "changed_files": changed_files,
        "ai_review": ai_review_text,
        "test_status": test_status
    }

    # Make Decision
    decision = check_if_auto_approvable(pr_data)

    if decision["auto_approve"]:
        print(f"\n✅ {decision['reason']}")
        msg = f"## ✅ Auto-Approval\n{decision['reason']}\n\n*Proceeding with automated merge sequence.*"
        post_comment(msg)
        # In a real pipeline, you would trigger the merge API here
    else:
        print(f"\n⏸️ {decision['reason']}")
        msg = f"## ⏸️ Manual Review Required\n**Reason:** {decision['reason']}\n\nAssigning to @{decision['assign_to']} for sign-off."
        post_comment(msg)
        assign_reviewer(decision["assign_to"])
        sys.exit(1) # Fail the job to block merge

if __name__ == "__main__":
    main()
