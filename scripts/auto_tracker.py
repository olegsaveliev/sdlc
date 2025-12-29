"""
Auto-Tracker for OpenAI API Usage
Wraps the OpenAI client to automatically track and report usage metrics.
"""

import os
import json
import time
import requests
from datetime import datetime
from typing import Optional

# ═══════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════

# Get from environment or use default
TRACKER_ENDPOINT = os.environ.get(
    'TRACKER_ENDPOINT',
    'https://api.jsonbin.io/v3/b/YOUR_BIN_ID'  # Will be replaced during setup
)

TRACKER_API_KEY = os.environ.get('TRACKER_API_KEY', '')

# Pricing per 1M tokens (update as needed)
PRICING = {
    'gpt-4': {'input': 30.0, 'output': 60.0},
    'gpt-4-turbo': {'input': 10.0, 'output': 30.0},
    'gpt-4o': {'input': 2.5, 'output': 10.0},
    'gpt-4o-mini': {'input': 0.15, 'output': 0.6},
    'gpt-3.5-turbo': {'input': 0.5, 'output': 1.5},
}

# ═══════════════════════════════════════════════════════════
# Core Tracking Functions
# ═══════════════════════════════════════════════════════════

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost based on model and tokens."""
    # Normalize model name
    model_base = model.split('-')[0:2]  # e.g., gpt-4 from gpt-4-0125-preview
    model_key = '-'.join(model_base)
    
    # Find matching pricing
    pricing = None
    for key in PRICING:
        if model.startswith(key):
            pricing = PRICING[key]
            break
    
    if not pricing:
        pricing = PRICING.get('gpt-4')  # Default fallback
    
    # Calculate cost (pricing is per 1M tokens)
    input_cost = (input_tokens / 1_000_000) * pricing['input']
    output_cost = (output_tokens / 1_000_000) * pricing['output']
    
    return round(input_cost + output_cost, 6)


def send_usage_data(data: dict) -> bool:
    """Send usage data to tracking endpoint."""
    if not TRACKER_ENDPOINT or 'YOUR_BIN_ID' in TRACKER_ENDPOINT:
        # Not configured yet, just log locally
        print(f"📊 [TRACKER] {json.dumps(data, indent=2)}")
        return False
    
    try:
        headers = {'Content-Type': 'application/json'}
        if TRACKER_API_KEY:
            headers['X-Master-Key'] = TRACKER_API_KEY
        
        # Step 1: GET current data from bin
        get_response = requests.get(
            TRACKER_ENDPOINT,
            headers=headers,
            timeout=10
        )
        
        if get_response.status_code == 200:
            response_data = get_response.json()
            
            # Handle JSONBin structure: response has 'record' key
            if isinstance(response_data, dict) and 'record' in response_data:
                record = response_data['record']
                
                # Check if data is nested under 'data' key
                if isinstance(record, dict) and 'data' in record:
                    records = record['data']
                elif isinstance(record, list):
                    records = record
                else:
                    records = []
            else:
                records = response_data if isinstance(response_data, list) else []
            
            # Ensure it's a list
            if not isinstance(records, list):
                records = []
            
            # Step 2: Append new data
            records.append(data)
            
            # Step 3: PUT updated data back
            # JSONBin expects data wrapped in appropriate structure
            put_data = {"data": records}
            
            put_response = requests.put(
                TRACKER_ENDPOINT,
                json=put_data,
                headers=headers,
                timeout=10
            )
            
            if put_response.status_code in [200, 201]:
                print(f"✅ [TRACKER] Data sent successfully")
                return True
            else:
                print(f"⚠️ [TRACKER] Failed to send (HTTP {put_response.status_code})")
                print(f"    Response: {put_response.text[:200]}")
                return False
        else:
            print(f"⚠️ [TRACKER] Failed to read bin (HTTP {get_response.status_code})")
            print(f"    Response: {get_response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"⚠️ [TRACKER] Error sending data: {e}")
        return False


def track_usage(
    model: str,
    input_tokens: int,
    output_tokens: int,
    agent_name: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """Track a single API usage event."""
    
    # Detect agent name from environment if not provided
    if not agent_name:
        agent_name = os.environ.get('AGENT_NAME', 'unknown')
        
        # Try to detect from GitHub Actions context
        if 'GITHUB_WORKFLOW' in os.environ:
            workflow = os.environ.get('GITHUB_WORKFLOW', '')
            if 'Unit Test' in workflow:
                agent_name = 'unit_tests'
            elif 'PR Review' in workflow:
                agent_name = 'pr_review'
            elif 'Automation Test' in workflow or 'Regression' in workflow:
                agent_name = 'auto_test'
    
    # Calculate cost
    cost = calculate_cost(model, input_tokens, output_tokens)
    total_tokens = input_tokens + output_tokens
    
    # Build tracking data
    data = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'agent': agent_name,
        'model': model,
        'tokens': {
            'input': input_tokens,
            'output': output_tokens,
            'total': total_tokens
        },
        'cost_usd': cost,
        'metadata': metadata or {},
        'environment': {
            'github_workflow': os.environ.get('GITHUB_WORKFLOW'),
            'github_run_id': os.environ.get('GITHUB_RUN_ID'),
            'github_repository': os.environ.get('GITHUB_REPOSITORY'),
        }
    }
    
    # Send to endpoint
    send_usage_data(data)
    
    return data


# ═══════════════════════════════════════════════════════════
# OpenAI Client Wrapper
# ═══════════════════════════════════════════════════════════

def track_openai(client):
    """
    Wrap an OpenAI client to automatically track usage.
    
    Usage:
        client = OpenAI(api_key="...")
        client = track_openai(client)  # Enable tracking
        
        # Now all API calls are automatically tracked
        response = client.chat.completions.create(...)
    """
    
    original_create = client.chat.completions.create
    
    def tracked_create(*args, **kwargs):
        """Wrapped create method that tracks usage."""
        
        # Call original method
        response = original_create(*args, **kwargs)
        
        # Extract usage info
        if hasattr(response, 'usage') and response.usage:
            usage = response.usage
            model = kwargs.get('model', response.model)
            
            # Track the usage
            track_usage(
                model=model,
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
                metadata={
                    'messages_count': len(kwargs.get('messages', [])),
                    'temperature': kwargs.get('temperature'),
                    'max_tokens': kwargs.get('max_tokens'),
                }
            )
        
        return response
    
    # Replace the method
    client.chat.completions.create = tracked_create
    
    print("🔍 [TRACKER] OpenAI client tracking enabled")
    return client


# ═══════════════════════════════════════════════════════════
# Manual Tracking Helper
# ═══════════════════════════════════════════════════════════

def log_usage(agent_name: str, model: str, input_tokens: int, output_tokens: int, **metadata):
    """
    Manually log usage (useful for non-OpenAI calls or custom tracking).
    
    Example:
        log_usage('my_agent', 'gpt-4', 1000, 500, task='code_review')
    """
    return track_usage(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        agent_name=agent_name,
        metadata=metadata
    )


# ═══════════════════════════════════════════════════════════
# Testing
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("Testing auto_tracker...")
    
    # Test cost calculation
    cost = calculate_cost('gpt-4', 1000, 500)
    print(f"Cost for 1000 input + 500 output tokens (GPT-4): ${cost}")
    
    # Test tracking
    track_usage(
        model='gpt-4',
        input_tokens=1000,
        output_tokens=500,
        agent_name='test_agent',
        metadata={'test': True}
    )
    
    print("\n✅ Auto-tracker working!")
