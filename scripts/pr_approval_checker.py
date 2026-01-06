#!/usr/bin/env python3
"""
PR Approval Checker
Determines if PR can be auto-approved or needs human review based on AI analysis.
"""

import os
import sys
import json
import requests
from typing import Dict, List, Any


# ═══════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_OWNER = os.environ.get('REPO_OWNER')
REPO_NAME = os.environ.get('REPO_NAME')
PR_NUMBER = os.environ.get('PR_NUMBER')
SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')

# Auto-approval configuration
MAX_FILES_FOR_AUTO_APPROVE = 3
LOW_RISK_EXTENSIONS = ('.md', '.txt', '.yml', '.yaml', '.json', '.gitignore')
LOW_RISK_PREFIXES = ('test_', 'tests/')
HIGH_RISK_KEYWORDS = ['auth', 'password', 'secret', 'token', 'credential', 'key', 'admin']


# ═══════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════

def get_pr_data() -> Dict[str, Any]:
    """Fetch PR data from GitHub API."""
    
    print("📥 Fetching PR data from GitHub...")
    
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{PR_NUMBER}"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        pr = response.json()
        
        # Get files changed
        files_url = f"{api_url}/files"
        files_response = requests.get(files_url, headers=headers, timeout=10)
        files_response.raise_for_status()
        files = files_response.json()
        
        # Get latest review comments
        comments_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{PR_NUMBER}/comments"
        comments_response = requests.get(comments_url, headers=headers, timeout=10)
        comments_response.raise_for_status()
        comments = comments_response.json()
        
        # Find AI review comment
        ai_review = ""
        for comment in reversed(comments):  # Get latest first
            if '🤖 AI Code Review' in comment.get('body', ''):
                ai_review = comment['body']
                break
        
        # Get check runs (test status)
        checks_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits/{pr['head']['sha']}/check-runs"
        checks_response = requests.get(checks_url, headers=headers, timeout=10)
        checks_response.raise_for_status()
        checks = checks_response.json()
        
        return {
            "pr": pr,
            "changed_files": [f['filename'] for f in files],
            "additions": sum(f['additions'] for f in files),
            "deletions": sum(f['deletions'] for f in files),
            "ai_review": ai_review,
            "checks": checks.get('check_runs', []),
            "labels": [label['name'] for label in pr.get('labels', [])]
        }
        
    except Exception as e:
        print(f"❌ Error fetching PR data: {e}")
        sys.exit(1)


def check_if_auto_approvable(pr_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine if PR can be auto-merged or needs human review.
    
    Returns dict with:
        - auto_approve: bool
        - reason: str
        - criteria_results: dict
        - assign_to: str (if needs review)
        - recommended_labels: list
    """
    
    print("\n" + "═" * 60)
    print("🔍 EVALUATING PR FOR AUTO-APPROVAL")
    print("═" * 60)
    
    changed_files = pr_data["changed_files"]
    ai_review = pr_data["ai_review"]
    checks = pr_data["checks"]
    
    # ─────────────────────────────────────────────────────────
    # Criterion 1: Small change (≤3 files)
    # ─────────────────────────────────────────────────────────
    small_change = len(changed_files) <= MAX_FILES_FOR_AUTO_APPROVE
    print(f"\n{'✅' if small_change else '❌'} Small change: {len(changed_files)} files (limit: {MAX_FILES_FOR_AUTO_APPROVE})")
    
    # ─────────────────────────────────────────────────────────
    # Criterion 2: Low-risk files only
    # ─────────────────────────────────────────────────────────
    def is_low_risk_file(filename: str) -> bool:
        """Check if file is low-risk."""
        # Check extension
        if any(filename.endswith(ext) for ext in LOW_RISK_EXTENSIONS):
            return True
        # Check if it's a test file
        if any(filename.startswith(prefix) for prefix in LOW_RISK_PREFIXES):
            return True
        return False
    
    low_risk_files = all(is_low_risk_file(f) for f in changed_files)
    
    if not low_risk_files:
        risky_files = [f for f in changed_files if not is_low_risk_file(f)]
        print(f"❌ Low-risk files: NO")
        print(f"   Risky files: {risky_files[:3]}")  # Show first 3
    else:
        print(f"✅ Low-risk files: YES (all {len(changed_files)} files are docs/tests/config)")
    
    # ─────────────────────────────────────────────────────────
    # Criterion 3: AI review passed
    # ─────────────────────────────────────────────────────────
    ai_review_passed = False
    if ai_review:
        # Check for positive indicators
        has_approval = "✅" in ai_review or "APPROVED" in ai_review
        has_critical = "🔴" in ai_review or "Critical" in ai_review
        
        ai_review_passed = has_approval and not has_critical
        
        print(f"{'✅' if ai_review_passed else '❌'} AI review passed: {ai_review_passed}")
        if has_critical:
            print(f"   ⚠️  Critical issues found in AI review")
    else:
        print(f"❌ AI review passed: NO (no AI review found)")
    
    # ─────────────────────────────────────────────────────────
    # Criterion 4: Tests passed
    # ─────────────────────────────────────────────────────────
    tests_passed = False
    if checks:
        # Check if all test-related checks passed
        test_checks = [
            c for c in checks 
            if any(keyword in c['name'].lower() for keyword in ['test', 'unit', 'regression'])
        ]
        
        if test_checks:
            tests_passed = all(c['conclusion'] == 'success' for c in test_checks)
            failed_tests = [c['name'] for c in test_checks if c['conclusion'] != 'success']
            
            print(f"{'✅' if tests_passed else '❌'} Tests passed: {len(test_checks)} checks")
            if failed_tests:
                print(f"   ⚠️  Failed: {failed_tests}")
        else:
            # No test checks found - assume OK for docs/config changes
            tests_passed = low_risk_files
            print(f"{'✅' if tests_passed else '⚠️ '} Tests passed: N/A (no test checks found)")
    else:
        print(f"⚠️  Tests passed: Unknown (no checks data)")
        tests_passed = False
    
    # ─────────────────────────────────────────────────────────
    # Criterion 5: No security-sensitive changes
    # ─────────────────────────────────────────────────────────
    def has_security_keywords(filename: str) -> bool:
        """Check if filename contains security-related keywords."""
        filename_lower = filename.lower()
        return any(keyword in filename_lower for keyword in HIGH_RISK_KEYWORDS)
    
    no_security_changes = not any(has_security_keywords(f) for f in changed_files)
    
    if not no_security_changes:
        security_files = [f for f in changed_files if has_security_keywords(f)]
        print(f"❌ No security changes: NO")
        print(f"   Security-sensitive files: {security_files}")
    else:
        print(f"✅ No security changes: YES")
    
    # ─────────────────────────────────────────────────────────
    # Additional checks
    # ─────────────────────────────────────────────────────────
    
    # Check change size
    total_changes = pr_data["additions"] + pr_data["deletions"]
    small_diff = total_changes <= 100
    print(f"\n{'✅' if small_diff else '⚠️ '} Change size: +{pr_data['additions']} -{pr_data['deletions']} (total: {total_changes})")
    
    # ─────────────────────────────────────────────────────────
    # Make decision
    # ─────────────────────────────────────────────────────────
    
    criteria = {
        "small_change": small_change,
        "low_risk_files": low_risk_files,
        "ai_review_passed": ai_review_passed,
        "tests_passed": tests_passed,
        "no_security_changes": no_security_changes
    }
    
    all_passed = all(criteria.values())
    
    print("\n" + "─" * 60)
    print(f"Overall: {'✅ ALL CRITERIA MET' if all_passed else '❌ SOME CRITERIA FAILED'}")
    print("─" * 60)
    
    if all_passed:
        return {
            "auto_approve": True,
            "reason": "✅ Low-risk change with all quality checks passed",
            "criteria_results": criteria,
            "recommended_labels": ["auto-approved", "ready-to-merge"],
            "confidence": "high"
        }
    else:
        failed = [k.replace('_', ' ').title() for k, v in criteria.items() if not v]
        
        # Determine reviewer based on what failed
        assign_to = "tech-lead"
        if not criteria["no_security_changes"]:
            assign_to = "security-team"
        elif not criteria["tests_passed"]:
            assign_to = "qa-team"
        
        return {
            "auto_approve": False,
            "reason": f"❌ Needs human review - Failed: {', '.join(failed)}",
            "criteria_results": criteria,
            "assign_to": assign_to,
            "recommended_labels": ["needs-review"],
            "confidence": "low" if len(failed) >= 3 else "medium"
        }


def add_pr_label(label: str):
    """Add label to PR."""
    
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{PR_NUMBER}/labels"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        response = requests.post(
            api_url,
            headers=headers,
            json={"labels": [label]},
            timeout=10
        )
        response.raise_for_status()
        print(f"   ✅ Added label: {label}")
    except Exception as e:
        print(f"   ⚠️  Could not add label '{label}': {e}")


def post_decision_comment(decision: Dict[str, Any], pr_data: Dict[str, Any]):
    """Post approval decision as PR comment."""
    
    print("\n📝 Posting decision to PR...")
    
    criteria_emoji = {
        "small_change": "📝",
        "low_risk_files": "🛡️",
        "ai_review_passed": "🤖",
        "tests_passed": "🧪",
        "no_security_changes": "🔒"
    }
    
    criteria_names = {
        "small_change": "Small Change",
        "low_risk_files": "Low-Risk Files",
        "ai_review_passed": "AI Review Passed",
        "tests_passed": "Tests Passed",
        "no_security_changes": "No Security Changes"
    }
    
    # Build criteria table
    criteria_rows = []
    for key, passed in decision["criteria_results"].items():
        emoji = criteria_emoji.get(key, "•")
        name = criteria_names.get(key, key)
        status = "✅ Pass" if passed else "❌ Fail"
        criteria_rows.append(f"| {emoji} {name} | {status} |")
    
    criteria_table = "\n".join(criteria_rows)
    
    if decision["auto_approve"]:
        comment = f"""## 🎉 Auto-Approval Recommendation

{decision['reason']}

### 📊 Approval Criteria

| Criterion | Status |
|-----------|--------|
{criteria_table}

**Confidence:** {decision['confidence'].upper()}

### 🏷️ Actions Taken
- Added labels: `{', '.join(decision['recommended_labels'])}`

### ✅ Next Steps
This PR meets all criteria for auto-approval. A team lead can merge when ready.

---
*🤖 Automated by PR Approval Checker*
"""
    else:
        comment = f"""## 👀 Human Review Required

{decision['reason']}

### 📊 Approval Criteria

| Criterion | Status |
|-----------|--------|
{criteria_table}

**Confidence:** {decision['confidence'].upper()}

### 👤 Recommended Reviewer
**{decision['assign_to'].replace('-', ' ').title()}** should review this PR.

### 🏷️ Actions Taken
- Added labels: `{', '.join(decision['recommended_labels'])}`

### 📋 Review Checklist
- [ ] Verify failed criteria above
- [ ] Check for security implications
- [ ] Confirm test coverage is adequate

---
*🤖 Automated by PR Approval Checker*
"""
    
    # Post to GitHub
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{PR_NUMBER}/comments"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        response = requests.post(
            api_url,
            headers=headers,
            json={"body": comment},
            timeout=10
        )
        response.raise_for_status()
        print("✅ Decision posted to PR")
    except Exception as e:
        print(f"⚠️  Could not post comment: {e}")


def send_slack_notification(decision: Dict[str, Any], pr_data: Dict[str, Any]):
    """Send Slack notification about approval decision."""
    
    if not SLACK_WEBHOOK:
        print("ℹ️  No SLACK_WEBHOOK configured, skipping Slack notification")
        return
    
    print("\n📨 Sending Slack notification...")
    
    pr_title = pr_data["pr"]["title"]
    pr_url = pr_data["pr"]["html_url"]
    pr_author = pr_data["pr"]["user"]["login"]
    
    if decision["auto_approve"]:
        message = {
            "text": f"✅ PR Auto-Approved: {pr_title}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ PR Auto-Approved!"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*PR:*\n<{pr_url}|{pr_title}>"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Author:*\n{pr_author}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Files Changed:*\n{len(pr_data['changed_files'])}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Confidence:*\n{decision['confidence'].upper()}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"✅ {decision['reason']}\n\nThis PR can be merged by a team lead."
                    }
                }
            ]
        }
    else:
        message = {
            "text": f"👀 PR Needs Review: {pr_title}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "👀 Human Review Required"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*PR:*\n<{pr_url}|{pr_title}>"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Author:*\n{pr_author}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Assign To:*\n{decision['assign_to'].replace('-', ' ').title()}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Confidence:*\n{decision['confidence'].upper()}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"⚠️ {decision['reason']}"
                    }
                }
            ]
        }
    
    try:
        response = requests.post(SLACK_WEBHOOK, json=message, timeout=10)
        response.raise_for_status()
        print("✅ Slack notification sent")
    except Exception as e:
        print(f"⚠️  Could not send Slack notification: {e}")


# ═══════════════════════════════════════════════════════════
# Main Function
# ═══════════════════════════════════════════════════════════

def main():
    """Main execution."""
    
    print("\n" + "═" * 60)
    print("🤖 PR APPROVAL CHECKER")
    print("═" * 60)
    
    # Validate environment
    if not all([GITHUB_TOKEN, REPO_OWNER, REPO_NAME, PR_NUMBER]):
        print("❌ Missing required environment variables:")
        print(f"   GITHUB_TOKEN: {'✓' if GITHUB_TOKEN else '✗'}")
        print(f"   REPO_OWNER: {'✓' if REPO_OWNER else '✗'}")
        print(f"   REPO_NAME: {'✓' if REPO_NAME else '✗'}")
        print(f"   PR_NUMBER: {'✓' if PR_NUMBER else '✗'}")
        sys.exit(1)
    
    print(f"\n📋 Configuration:")
    print(f"   Repository: {REPO_OWNER}/{REPO_NAME}")
    print(f"   PR Number: #{PR_NUMBER}")
    print(f"   Slack: {'Enabled' if SLACK_WEBHOOK else 'Disabled'}")
    
    # Get PR data
    pr_data = get_pr_data()
    
    # Check if auto-approvable
    decision = check_if_auto_approvable(pr_data)
    
    # Add labels
    print(f"\n🏷️  Adding labels...")
    for label in decision["recommended_labels"]:
        add_pr_label(label)
    
    # Post decision comment
    post_decision_comment(decision, pr_data)
    
    # Send Slack notification
    send_slack_notification(decision, pr_data)
    
    # Output for GitHub Actions
    print(f"\n📤 Setting output variables:")
    print(f"   auto_approve={str(decision['auto_approve']).lower()}")
    print(f"   confidence={decision['confidence']}")
    
    # Set GitHub Actions output
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"auto_approve={str(decision['auto_approve']).lower()}\n")
            f.write(f"confidence={decision['confidence']}\n")
            f.write(f"reason={decision['reason']}\n")
    
    print("\n" + "═" * 60)
    if decision["auto_approve"]:
        print("✅ PR CAN BE AUTO-APPROVED")
    else:
        print("👀 PR NEEDS HUMAN REVIEW")
    print("═" * 60)
    print()


if __name__ == '__main__':
    main()
