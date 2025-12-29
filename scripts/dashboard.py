#!/usr/bin/env python3
"""
Simple AI Agent Cost Dashboard
Auto-updates from metrics.json - zero configuration needed!

Usage:
    python dashboard.py
    
Then open: http://localhost:5001
"""

from flask import Flask, render_template_string, jsonify
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

app = Flask(__name__)

# Config
METRICS_FILE = Path(__file__).parent / 'metrics.json'
AUTO_REFRESH_SECONDS = 30

# Pricing for cost comparison
PRICING = {
    'GPT-4': {'input': 30.00, 'output': 60.00, 'color': '#10b981'},
    'GPT-4o': {'input': 2.50, 'output': 10.00, 'color': '#059669'},
    'GPT-4o mini': {'input': 0.150, 'output': 0.600, 'color': '#34d399'},
    'Claude Sonnet 4': {'input': 3.00, 'output': 15.00, 'color': '#667eea'},
    'Claude Opus 4': {'input': 15.00, 'output': 75.00, 'color': '#9333ea'},
}

def load_metrics():
    """Load metrics from JSON file"""
    if not METRICS_FILE.exists():
        return []
    
    try:
        with open(METRICS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def calculate_stats(metrics):
    """Calculate dashboard statistics"""
    if not metrics:
        return {
            'total_cost': 0,
            'total_tokens': 0,
            'total_calls': 0,
            'agents': {},
            'recent_activity': [],
            'daily_costs': {},
            'cost_comparison': {},
            'last_updated': 'No data yet'
        }
    
    # Basic stats
    total_cost = sum(m['cost'] for m in metrics)
    total_tokens = sum(m['total_tokens'] for m in metrics)
    total_calls = len(metrics)
    
    # Per-agent stats
    agents = defaultdict(lambda: {'calls': 0, 'tokens': 0, 'cost': 0})
    for m in metrics:
        agent = m['agent']
        agents[agent]['calls'] += 1
        agents[agent]['tokens'] += m['total_tokens']
        agents[agent]['cost'] += m['cost']
    
    # Daily costs (last 30 days)
    cutoff = datetime.now() - timedelta(days=30)
    daily_costs = defaultdict(float)
    
    for m in metrics:
        try:
            timestamp = datetime.fromisoformat(m['timestamp'])
            if timestamp >= cutoff:
                date_key = timestamp.strftime('%Y-%m-%d')
                daily_costs[date_key] += m['cost']
        except:
            pass
    
    # Recent activity (last 20)
    recent_activity = sorted(metrics, key=lambda x: x['timestamp'], reverse=True)[:20]
    
    # Cost comparison
    total_input = sum(m['input_tokens'] for m in metrics)
    total_output = sum(m['output_tokens'] for m in metrics)
    
    cost_comparison = {}
    for model, pricing in PRICING.items():
        alt_cost = (total_input / 1_000_000 * pricing['input']) + (total_output / 1_000_000 * pricing['output'])
        savings = total_cost - alt_cost
        cost_comparison[model] = {
            'cost': alt_cost,
            'savings': savings,
            'savings_pct': (savings / total_cost * 100) if total_cost > 0 else 0,
            'color': pricing['color']
        }
    
    return {
        'total_cost': total_cost,
        'total_tokens': total_tokens,
        'total_calls': total_calls,
        'agents': dict(agents),
        'recent_activity': recent_activity,
        'daily_costs': dict(daily_costs),
        'cost_comparison': cost_comparison,
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Agent Cost Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .header .last-update {
            opacity: 0.9;
            font-size: 0.9rem;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }
        
        .stat-card h3 {
            color: #667eea;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #2d3748;
        }
        
        .stat-label {
            color: #718096;
            font-size: 0.9rem;
            margin-top: 5px;
        }
        
        .chart-container {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .chart-container h2 {
            color: #2d3748;
            margin-bottom: 20px;
            font-size: 1.5rem;
        }
        
        .chart-wrapper {
            height: 300px;
            position: relative;
        }
        
        .agents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .agent-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .agent-card h3 {
            color: #667eea;
            font-size: 1.2rem;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .agent-stat {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .agent-stat:last-child {
            border-bottom: none;
        }
        
        .agent-stat-label {
            color: #718096;
            font-size: 0.9rem;
        }
        
        .agent-stat-value {
            font-weight: bold;
            color: #2d3748;
        }
        
        .activity-container {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .activity-container h2 {
            color: #2d3748;
            margin-bottom: 20px;
            font-size: 1.5rem;
        }
        
        .activity-item {
            padding: 15px;
            border-bottom: 1px solid #e2e8f0;
            transition: background 0.2s;
        }
        
        .activity-item:hover {
            background: #f7fafc;
        }
        
        .activity-item:last-child {
            border-bottom: none;
        }
        
        .activity-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .activity-agent {
            font-weight: bold;
            color: #2d3748;
        }
        
        .activity-badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: bold;
        }
        
        .badge-success {
            background: #d1fae5;
            color: #065f46;
        }
        
        .badge-failed {
            background: #fee2e2;
            color: #991b1b;
        }
        
        .activity-meta {
            display: flex;
            gap: 20px;
            font-size: 0.85rem;
            color: #718096;
        }
        
        .cost-comparison {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .comparison-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .comparison-item:last-child {
            border-bottom: none;
        }
        
        .comparison-model {
            font-weight: 500;
            color: #2d3748;
        }
        
        .comparison-savings {
            display: flex;
            gap: 20px;
            align-items: center;
        }
        
        .savings-positive {
            color: #059669;
            font-weight: bold;
        }
        
        .savings-negative {
            color: #dc2626;
            font-weight: bold;
        }
        
        @media (max-width: 768px) {
            .header h1 { font-size: 1.8rem; }
            .stats-grid { grid-template-columns: 1fr; }
            .agents-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Agent Cost Dashboard</h1>
            <p class="last-update">Last updated: <span id="lastUpdate">{{ last_updated }}</span></p>
            <p style="margin-top: 10px; opacity: 0.8;">Auto-refresh: {{ refresh_seconds }}s</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Cost</h3>
                <div class="stat-value" id="totalCost">$0.00</div>
                <div class="stat-label">All time</div>
            </div>
            
            <div class="stat-card">
                <h3>Total Tokens</h3>
                <div class="stat-value" id="totalTokens">0</div>
                <div class="stat-label">Total processed</div>
            </div>
            
            <div class="stat-card">
                <h3>Total Calls</h3>
                <div class="stat-value" id="totalCalls">0</div>
                <div class="stat-label">API requests</div>
            </div>
            
            <div class="stat-card">
                <h3>Active Agents</h3>
                <div class="stat-value" id="activeAgents">0</div>
                <div class="stat-label">Unique agents</div>
            </div>
        </div>

        <div class="chart-container">
            <h2>💰 Daily Cost Trend</h2>
            <div class="chart-wrapper">
                <canvas id="costChart"></canvas>
            </div>
        </div>

        <div id="agentsContainer" class="agents-grid"></div>

        <div class="cost-comparison">
            <h2>📊 Cost Comparison (Alternative Models)</h2>
            <div id="comparisonContainer"></div>
        </div>

        <div class="activity-container">
            <h2>📋 Recent Activity</h2>
            <div id="activityContainer"></div>
        </div>
    </div>

    <script>
        const REFRESH_INTERVAL = {{ refresh_seconds }} * 1000;
        let chart = null;

        async function fetchData() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Failed to fetch data:', error);
            }
        }

        function updateDashboard(data) {
            // Update summary stats
            document.getElementById('totalCost').textContent = '$' + data.total_cost.toFixed(2);
            document.getElementById('totalTokens').textContent = data.total_tokens.toLocaleString();
            document.getElementById('totalCalls').textContent = data.total_calls.toLocaleString();
            document.getElementById('activeAgents').textContent = Object.keys(data.agents).length;
            document.getElementById('lastUpdate').textContent = data.last_updated;

            // Update agents
            updateAgents(data.agents);

            // Update charts
            updateCostChart(data.daily_costs);

            // Update cost comparison
            updateCostComparison(data.cost_comparison);

            // Update activity
            updateActivity(data.recent_activity);
        }

        function updateAgents(agents) {
            const container = document.getElementById('agentsContainer');
            container.innerHTML = '';

            Object.entries(agents).forEach(([name, stats]) => {
                const card = document.createElement('div');
                card.className = 'agent-card';
                card.innerHTML = `
                    <h3>🤖 ${name}</h3>
                    <div class="agent-stat">
                        <span class="agent-stat-label">Total Calls</span>
                        <span class="agent-stat-value">${stats.calls}</span>
                    </div>
                    <div class="agent-stat">
                        <span class="agent-stat-label">Tokens Used</span>
                        <span class="agent-stat-value">${stats.tokens.toLocaleString()}</span>
                    </div>
                    <div class="agent-stat">
                        <span class="agent-stat-label">Total Cost</span>
                        <span class="agent-stat-value" style="color: #059669;">$${stats.cost.toFixed(2)}</span>
                    </div>
                `;
                container.appendChild(card);
            });
        }

        function updateCostChart(dailyCosts) {
            const dates = Object.keys(dailyCosts).sort();
            const costs = dates.map(d => dailyCosts[d]);

            const ctx = document.getElementById('costChart');
            if (chart) chart.destroy();

            chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: dates.map(d => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
                    datasets: [{
                        label: 'Daily Cost',
                        data: costs,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { callback: (value) => '$' + value.toFixed(2) }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }

        function updateCostComparison(comparison) {
            const container = document.getElementById('comparisonContainer');
            
            // Sort by savings
            const sorted = Object.entries(comparison).sort((a, b) => b[1].savings - a[1].savings);
            
            container.innerHTML = sorted.map(([model, data]) => {
                const savingsClass = data.savings > 0 ? 'savings-positive' : 'savings-negative';
                const savingsPrefix = data.savings > 0 ? 'Save' : 'Cost';
                
                return `
                    <div class="comparison-item">
                        <span class="comparison-model">${model}</span>
                        <div class="comparison-savings">
                            <span>$${data.cost.toFixed(2)}</span>
                            <span class="${savingsClass}">
                                ${savingsPrefix} $${Math.abs(data.savings).toFixed(2)} (${Math.abs(data.savings_pct).toFixed(1)}%)
                            </span>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function updateActivity(activity) {
            const container = document.getElementById('activityContainer');
            
            if (activity.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #999;">No activity yet</p>';
                return;
            }

            container.innerHTML = activity.map(item => {
                const badgeClass = item.status === 'Success' ? 'badge-success' : 'badge-failed';
                const timestamp = new Date(item.timestamp).toLocaleString();
                
                return `
                    <div class="activity-item">
                        <div class="activity-header">
                            <span class="activity-agent">🤖 ${item.agent}</span>
                            <span class="activity-badge ${badgeClass}">${item.status}</span>
                        </div>
                        <div class="activity-meta">
                            <span>⏱️ ${item.execution_time.toFixed(2)}s</span>
                            <span>🔢 ${item.total_tokens.toLocaleString()} tokens</span>
                            <span>💰 $${item.cost.toFixed(4)}</span>
                            <span>📅 ${timestamp}</span>
                        </div>
                    </div>
                `;
            }).join('');
        }

        // Initial fetch and auto-refresh
        fetchData();
        setInterval(fetchData, REFRESH_INTERVAL);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    metrics = load_metrics()
    stats = calculate_stats(metrics)
    return render_template_string(
        HTML_TEMPLATE,
        refresh_seconds=AUTO_REFRESH_SECONDS,
        last_updated=stats['last_updated']
    )

@app.route('/api/metrics')
def api_metrics():
    metrics = load_metrics()
    return jsonify(calculate_stats(metrics))

def main():
    print("\n🎨 AI Agent Cost Dashboard - Simple Edition")
    print("=" * 70)
    
    if not METRICS_FILE.exists():
        print("⚠️  No metrics file found yet.")
        print("   Metrics will appear once your agents start running!")
    else:
        metrics = load_metrics()
        print(f"✅ Loaded {len(metrics)} metrics from {METRICS_FILE}")
    
    print(f"\n🔄 Auto-refresh: Every {AUTO_REFRESH_SECONDS} seconds")
    print(f"🌐 Dashboard: http://localhost:5001")
    print(f"🛑 Stop: Press Ctrl+C")
    print("=" * 70)
    print()
    
    try:
        app.run(host='0.0.0.0', port=5001, debug=False)
    except KeyboardInterrupt:
        print("\n\n✅ Dashboard stopped")

if __name__ == '__main__':
    main()
