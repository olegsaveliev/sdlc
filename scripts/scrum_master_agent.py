#!/usr/bin/env python3
"""
AI Scrum Master - Daily Standup Report Generator
Tracks usage automatically to dashboard
Uses 3-Question Template format
"""

import os
import git
import requests
from openai import OpenAI
from datetime import datetime, timedelta
from auto_tracker import track_openai  # Auto-tracking import

def main():
    """Generate and send daily standup report."""
    
    # ═══════════════════════════════════════════════════════════
    # STEP 1: Get Git Logs (Last 24 Hours)
    # ═══════════════════════════════════════════════════════════
    
    print("📊 Generating Daily Standup Report...")
    print()
    
    try:
        repo = git.Repo('.')
        cutoff = datetime.now() - timedelta(hours=24)
        commits = [
            c for c in repo.iter_commits() 
            if datetime.fromtimestamp(c.committed_date) > cutoff
        ]
        
        if commits:
            log_text = '\n'.join([
                f'- {c.summary} (by {c.author.name})' 
                for c in commits
            ])
            print(f"✅ Found {len(commits)} commits in last 24 hours")
        else:
            log_text = 'No commits in the last 24 hours.'
            print("ℹ️  No commits today")
            
    except Exception as e:
        log_text = f'Error reading git logs: {e}'
        print(f"⚠️  Error: {e}")
    
    print()
    
    # ═══════════════════════════════════════════════════════════
    # STEP 2: Ask AI for Summary (with tracking)
    # ═══════════════════════════════════════════════════════════
    
    print("🤖 Generating AI summary with 3-question template...")
    
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    client = track_openai(client)  # Enable auto-tracking
    
    # Updated prompt for 3-Question Template
    prompt = f"""You are a Scrum Master generating a Daily Standup Report based on git commits.

Analyze these commits and create a standup report using the **3-Question Template**:

Format your response EXACTLY like this:

*🏃 Daily Standup Report - {datetime.now().strftime('%B %d, %Y')}*

*✅ Yesterday: What did you complete?*
[List completed work based on commits - be specific]

*🎯 Today: What are you working on?*
[Based on commit patterns, infer what's likely next - or say "Continuing work on..." if unclear]

*🚫 Blockers: Is anything stopping your progress?*
[Identify potential issues from commits - or say "No blockers identified"]

---

Git commits from the last 24 hours:
{log_text}

Instructions:
- Be concise but specific
- Use bullet points for multiple items
- Infer "Today" from commit patterns (e.g., if fixing bugs → "Continue testing and bug fixes")
- For blockers, look for: error messages, reverts, multiple attempts, or say "No blockers identified"
- If no commits, acknowledge it positively: "No commits yet - planning/research phase"
"""
    
    try:
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7
        )
        
        report = response.choices[0].message.content
        print("✅ Report generated")
        
    except Exception as e:
        # Fallback report if AI fails
        report = f"""*🏃 Daily Standup Report - {datetime.now().strftime('%B %d, %Y')}*

*✅ Yesterday: What did you complete?*
{log_text}

*🎯 Today: What are you working on?*
Continuing development work

*🚫 Blockers: Is anything stopping your progress?*
⚠️ AI report generation failed: {e}
"""
        print(f"⚠️  AI generation failed: {e}")
    
    print()
    
    # ═══════════════════════════════════════════════════════════
    # STEP 3: Send to Slack
    # ═══════════════════════════════════════════════════════════
    
    slack_webhook = os.getenv('SLACK_WEBHOOK')
    
    if slack_webhook:
        print("📨 Sending to Slack...")
        
        try:
            response = requests.post(
                slack_webhook,
                json={'text': report},
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
        print(report)
        print("=" * 60)
    
    print()
    print("✅ Daily standup report complete!")


if __name__ == '__main__':
    main()
