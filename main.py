from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

# Calculator functions
def add(a, b):
    """Add two numbers"""
    return a + b

def subtract(a, b):
    """Subtract two numbers"""
    return a - b

app = FastAPI(title="Calculator API - Staging")

# Serve the HTML interface
@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Calculator API - Staging Environment</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 100%;
        }
        
        h1 {
            color: #667eea;
            margin-bottom: 10px;
            text-align: center;
        }
        
        .status {
            background: #10b981;
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            display: inline-block;
            margin: 20px 0;
            font-size: 14px;
            font-weight: 600;
        }
        
        .calculator {
            margin-top: 30px;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #4b5563;
            font-weight: 600;
            font-size: 14px;
        }
        
        input[type="number"] {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 16px;
            transition: all 0.3s;
        }
        
        input[type="number"]:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .button-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 25px 0;
        }
        
        button {
            padding: 14px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            color: white;
        }
        
        .btn-add {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        }
        
        .btn-add:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(16, 185, 129, 0.3);
        }
        
        .btn-subtract {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        }
        
        .btn-subtract:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(245, 158, 11, 0.3);
        }
        
        .result {
            background: #f3f4f6;
            padding: 20px;
            border-radius: 10px;
            margin-top: 25px;
            text-align: center;
            min-height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
        }
        
        .result-label {
            color: #6b7280;
            font-size: 14px;
            margin-bottom: 8px;
        }
        
        .result-value {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }
        
        .api-info {
            background: #eff6ff;
            border-left: 4px solid #3b82f6;
            padding: 15px;
            margin-top: 30px;
            border-radius: 5px;
        }
        
        .api-info h3 {
            color: #1e40af;
            margin-bottom: 10px;
            font-size: 16px;
        }
        
        .api-info code {
            background: #dbeafe;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 13px;
            color: #1e40af;
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #9ca3af;
            font-size: 13px;
        }
        
        .error {
            color: #dc2626;
            font-size: 14px;
            margin-top: 10px;
            display: none;
        }
        
        .loading {
            display: none;
            color: #667eea;
            font-size: 14px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧮 Calculator API</h1>
        <div style="text-align: center;">
            <span class="status">✅ Staging Environment - LIVE</span>
        </div>
        
        <div class="calculator">
            <div class="input-group">
                <label for="num1">First Number</label>
                <input type="number" id="num1" placeholder="Enter first number" value="10">
            </div>
            
            <div class="input-group">
                <label for="num2">Second Number</label>
                <input type="number" id="num2" placeholder="Enter second number" value="5">
            </div>
            
            <div class="button-group">
                <button class="btn-add" onclick="calculate('add')">➕ Add</button>
                <button class="btn-subtract" onclick="calculate('subtract')">➖ Subtract</button>
            </div>
            
            <div class="loading" id="loading">⏳ Calculating...</div>
            <div class="error" id="error"></div>
            
            <div class="result" id="result">
                <div class="result-label">Result</div>
                <div class="result-value" id="resultValue">-</div>
            </div>
        </div>
        
        <div class="api-info">
            <h3>📡 API Endpoints</h3>
            <p style="margin: 5px 0;"><strong>Add:</strong> <code>GET /add?a={num1}&b={num2}</code></p>
            <p style="margin: 5px 0;"><strong>Subtract:</strong> <code>GET /subtract?a={num1}&b={num2}</code></p>
            <p style="margin: 5px 0;"><strong>Docs:</strong> <code>GET /docs</code></p>
        </div>
        
        <div class="footer">
            Deployed via GitHub Actions to AWS ECS Fargate<br>
            Last Updated: <span id="timestamp"></span>
        </div>
    </div>
    
    <script>
        // Set timestamp
        document.getElementById('timestamp').textContent = new Date().toLocaleString();
        
        async function calculate(operation) {
            const num1 = parseFloat(document.getElementById('num1').value);
            const num2 = parseFloat(document.getElementById('num2').value);
            const loading = document.getElementById('loading');
            const error = document.getElementById('error');
            const resultValue = document.getElementById('resultValue');
            
            // Reset states
            loading.style.display = 'block';
            error.style.display = 'none';
            resultValue.textContent = '-';
            
            // Validate inputs
            if (isNaN(num1) || isNaN(num2)) {
                error.textContent = 'Please enter valid numbers';
                error.style.display = 'block';
                loading.style.display = 'none';
                return;
            }
            
            try {
                const response = await fetch(`/${operation}?a=${num1}&b=${num2}`);
                const data = await response.json();
                
                if (response.ok) {
                    resultValue.textContent = data.result;
                    
                    // Animate result
                    resultValue.style.transform = 'scale(1.2)';
                    setTimeout(() => {
                        resultValue.style.transform = 'scale(1)';
                    }, 200);
                } else {
                    error.textContent = data.detail || 'Calculation failed';
                    error.style.display = 'block';
                }
            } catch (err) {
                error.textContent = 'Error connecting to API: ' + err.message;
                error.style.display = 'block';
            } finally {
                loading.style.display = 'none';
            }
        }
        
        // Allow Enter key to trigger calculation
        document.getElementById('num2').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                calculate('add');
            }
        });
    </script>
</body>
</html>
    """
    return html_content


@app.get("/add")
async def api_add(a: float, b: float):
    """Add two numbers"""
    result = add(a, b)
    return {"operation": "add", "a": a, "b": b, "result": result}


@app.get("/subtract")
async def api_subtract(a: float, b: float):
    """Subtract two numbers"""
    result = subtract(a, b)
    return {"operation": "subtract", "a": a, "b": b, "result": result}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "calculator-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
