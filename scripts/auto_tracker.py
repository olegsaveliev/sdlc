#!/usr/bin/env python3
"""
Auto-Tracking Wrapper for AI Agents
Automatically tracks all AI calls with zero manual work.

Just import and wrap your OpenAI client:
    from auto_tracker import track_openai
    client = track_openai(OpenAI())
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from functools import wraps

# Storage path
METRICS_FILE = Path(__file__).parent / 'metrics.json'

# Pricing per million tokens
PRICING = {
    'gpt-4': {'input': 30.00, 'output': 60.00},
    'gpt-4o': {'input': 2.50, 'output': 10.00},
    'gpt-4o-mini': {'input': 0.150, 'output': 0.600},
    'claude-sonnet-4': {'input': 3.00, 'output': 15.00},
    'claude-opus-4': {'input': 15.00, 'output': 75.00},
}

def get_agent_name():
    """Auto-detect agent name from environment or script name"""
    # Try GitHub Actions context first
    workflow_name = os.getenv('GITHUB_WORKFLOW', '')
    if 'pr' in workflow_name.lower() or 'review' in workflow_name.lower():
        return 'PR Review Agent'
    elif 'unit' in workflow_name.lower() or 'test' in workflow_name.lower():
        return 'Unit Test Generator'
    elif 'regression' in workflow_name.lower() or 'autotest' in workflow_name.lower():
        return 'Regression Test Generator'
    elif 'scrum' in workflow_name.lower():
        return 'Scrum Master Bot'
    
    # Fallback to script name
    import sys
    script_name = Path(sys.argv[0]).stem
    return script_name.replace('_', ' ').title()

def log_metric(agent_name, model, input_tokens, output_tokens, execution_time, status='Success'):
    """Log a single metric to JSON file"""
    
    # Calculate cost
    model_key = model.lower()
    if 'gpt-4o-mini' in model_key:
        pricing = PRICING['gpt-4o-mini']
    elif 'gpt-4o' in model_key:
        pricing = PRICING['gpt-4o']
    elif 'gpt-4' in model_key:
        pricing = PRICING['gpt-4']
    elif 'claude-sonnet' in model_key:
        pricing = PRICING['claude-sonnet-4']
    elif 'claude-opus' in model_key:
        pricing = PRICING['claude-opus-4']
    else:
        pricing = PRICING['gpt-4']  # Default
    
    cost = (input_tokens / 1_000_000 * pricing['input']) + (output_tokens / 1_000_000 * pricing['output'])
    
    # Create metric entry
    metric = {
        'timestamp': datetime.now().isoformat(),
        'agent': agent_name,
        'model': model,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'total_tokens': input_tokens + output_tokens,
        'cost': round(cost, 6),
        'execution_time': execution_time,
        'status': status,
        'run_id': os.getenv('GITHUB_RUN_ID', 'local'),
        'pr_number': os.getenv('PR_NUMBER', ''),
    }
    
    # Load existing metrics
    if METRICS_FILE.exists():
        with open(METRICS_FILE, 'r') as f:
            try:
                metrics = json.load(f)
            except:
                metrics = []
    else:
        metrics = []
    
    # Append new metric
    metrics.append(metric)
    
    # Keep only last 1000 entries
    metrics = metrics[-1000:]
    
    # Save
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"✅ Tracked: {agent_name} | {input_tokens + output_tokens:,} tokens | ${cost:.4f}")
    
    return metric

def track_openai(client):
    """Wrap OpenAI client to auto-track all calls"""
    
    original_create = client.chat.completions.create
    
    @wraps(original_create)
    def wrapped_create(*args, **kwargs):
        agent_name = get_agent_name()
        start_time = time.time()
        
        try:
            # Make the actual API call
            response = original_create(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Extract usage info
            model = kwargs.get('model', 'gpt-4')
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            
            # Log automatically
            log_metric(
                agent_name=agent_name,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                execution_time=execution_time,
                status='Success'
            )
            
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ API call failed: {e}")
            
            # Log failure
            log_metric(
                agent_name=agent_name,
                model=kwargs.get('model', 'gpt-4'),
                input_tokens=0,
                output_tokens=0,
                execution_time=execution_time,
                status='Failed'
            )
            
            raise
    
    client.chat.completions.create = wrapped_create
    return client

def track_anthropic(client):
    """Wrap Anthropic client to auto-track all calls"""
    
    original_create = client.messages.create
    
    @wraps(original_create)
    def wrapped_create(*args, **kwargs):
        agent_name = get_agent_name()
        start_time = time.time()
        
        try:
            # Make the actual API call
            response = original_create(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Extract usage info
            model = kwargs.get('model', 'claude-sonnet-4')
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            
            # Log automatically
            log_metric(
                agent_name=agent_name,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                execution_time=execution_time,
                status='Success'
            )
            
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ API call failed: {e}")
            
            # Log failure
            log_metric(
                agent_name=agent_name,
                model=kwargs.get('model', 'claude-sonnet-4'),
                input_tokens=0,
                output_tokens=0,
                execution_time=execution_time,
                status='Failed'
            )
            
            raise
    
    client.messages.create = wrapped_create
    return client

# CLI for manual tracking
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Test tracking
        print("Testing auto-tracker...")
        log_metric(
            agent_name='Test Agent',
            model='gpt-4',
            input_tokens=1000,
            output_tokens=500,
            execution_time=2.5,
            status='Success'
        )
        print(f"✅ Metric saved to {METRICS_FILE}")
