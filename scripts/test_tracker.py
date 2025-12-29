#!/usr/bin/env python3
"""
Quick Test - Verify Auto-Tracking is Working
Run this to diagnose issues
"""

import os
import sys
from pathlib import Path

print("\n" + "="*60)
print("🔍 TROUBLESHOOTING AUTO-TRACKER")
print("="*60)

# Check 1: File locations
print("\n1. Checking file locations...")
current_dir = Path.cwd()
print(f"   Current directory: {current_dir}")

auto_tracker_path = current_dir / "auto_tracker.py"
dashboard_path = current_dir / "dashboard.py"
metrics_path = current_dir / "metrics.json"

if auto_tracker_path.exists():
    print(f"   ✅ auto_tracker.py found")
else:
    print(f"   ❌ auto_tracker.py NOT FOUND")
    print(f"      Expected at: {auto_tracker_path}")

if dashboard_path.exists():
    print(f"   ✅ dashboard.py found")
else:
    print(f"   ❌ dashboard.py NOT FOUND")

if metrics_path.exists():
    print(f"   ✅ metrics.json found")
    import json
    try:
        with open(metrics_path) as f:
            data = json.load(f)
        print(f"      Contains {len(data)} metrics")
        if data:
            print(f"      Latest: {data[-1]['agent']} - ${data[-1]['cost']:.4f}")
    except Exception as e:
        print(f"      ⚠️ Error reading: {e}")
else:
    print(f"   ℹ️  metrics.json not created yet (will be created on first run)")

# Check 2: Test import
print("\n2. Testing auto_tracker import...")
try:
    from auto_tracker import track_openai, log_metric
    print("   ✅ Import successful")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    print("   Make sure auto_tracker.py is in the same directory")
    sys.exit(1)

# Check 3: Test tracking
print("\n3. Testing tracking function...")
try:
    from auto_tracker import log_metric
    
    result = log_metric(
        agent_name="Test Agent",
        model="gpt-4",
        input_tokens=1000,
        output_tokens=500,
        execution_time=2.5,
        status="Success"
    )
    
    print(f"   ✅ Tracking works! Cost: ${result['cost']:.4f}")
    print(f"   Saved to: {metrics_path}")
    
except Exception as e:
    print(f"   ❌ Tracking failed: {e}")
    import traceback
    traceback.print_exc()

# Check 4: Verify metrics.json
print("\n4. Verifying metrics.json...")
if metrics_path.exists():
    with open(metrics_path) as f:
        data = json.load(f)
    print(f"   ✅ File readable, contains {len(data)} metrics")
    
    # Show last 3 entries
    print("\n   Last 3 entries:")
    for entry in data[-3:]:
        print(f"   - {entry['timestamp'][:19]} | {entry['agent']} | ${entry['cost']:.4f}")
else:
    print("   ❌ metrics.json not created")

# Check 5: Test with actual OpenAI call (if API key available)
print("\n5. Testing with actual OpenAI call...")
api_key = os.getenv('OPENAI_KEY')
if api_key:
    print("   ✅ OPENAI_KEY found, attempting test call...")
    try:
        from openai import OpenAI
        from auto_tracker import track_openai
        
        client = OpenAI(api_key=api_key)
        client = track_openai(client)
        
        print("   Making test API call...")
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': 'Say hello'}],
            max_tokens=10
        )
        
        print(f"   ✅ API call successful!")
        print(f"   Response: {response.choices[0].message.content}")
        print(f"   Check metrics.json - should have new entry")
        
    except Exception as e:
        print(f"   ❌ API call failed: {e}")
else:
    print("   ℹ️  OPENAI_KEY not set, skipping API test")

# Summary
print("\n" + "="*60)
print("📋 SUMMARY")
print("="*60)

if metrics_path.exists():
    with open(metrics_path) as f:
        data = json.load(f)
    
    if len(data) > 0:
        print(f"✅ Tracking is working! {len(data)} metrics recorded.")
        print(f"\nTo view dashboard:")
        print(f"   python dashboard.py")
        print(f"   Open: http://localhost:5001")
    else:
        print("⚠️  Tracking setup complete but no metrics yet.")
        print("   Run your agents (pr_review_agent.py, etc.) to generate metrics.")
else:
    print("❌ Setup incomplete. Check errors above.")

print("\n" + "="*60 + "\n")
