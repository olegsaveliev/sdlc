from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

### Calculator functions
def add(a, b):
    """Add two numbers"""
    return a + b

def subtract(a, b):
    """Subtract two numbers"""
    return a - b

def multiply(a, b):
    """Multiply two numbers"""
    return a * b

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
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
            background: #f5f5f7;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .container {
            background: white;
            padding: 48px;
            border-radius: 18px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 10px 20px rgba(0, 0, 0, 0.05);
            max-width: 420px;
            width: 100%;
        }

        h1 {
            color: #1d1d1f;
            margin-bottom: 8px;
            text-align: center;
            font-size: 28px;
            font-weight: 600;
            letter-spacing: -0.5px;
        }

        .status {
            background: #f5f5f7;
            color: #86868b;
            padding: 6px 12px;
            border-radius: 12px;
            display: inline-block;
            margin: 12px 0 32px;
            font-size: 12px;
            font-weight: 500;
            letter-spacing: 0.2px;
        }

        .calculator {
            margin-top: 0;
        }

        .input-group {
            margin-bottom: 16px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            color: #1d1d1f;
            font-weight: 500;
            font-size: 14px;
            letter-spacing: -0.1px;
        }

        input[type="number"] {
            width: 100%;
            padding: 12px 16px;
            border: 1px solid #d2d2d7;
            border-radius: 10px;
            font-size: 17px;
            transition: all 0.2s ease;
            background: #fafafa;
        }

        input[type="number"]:focus {
            outline: none;
            border-color: #0071e3;
            background: white;
            box-shadow: 0 0 0 4px rgba(0, 113, 227, 0.1);
        }

        input[type="number"]::placeholder {
            color: #86868b;
        }

        .button-group {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 12px;
            margin: 28px 0 20px;
        }

        button {
            padding: 12px 20px;
            border: none;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            letter-spacing: -0.2px;
        }

        .btn-add {
            background: #0071e3;
            color: white;
        }

        .btn-add:hover {
            background: #0077ed;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 113, 227, 0.25);
        }

        .btn-subtract {
            background: #0071e3;
            color: white;
        }

        .btn-subtract:hover {
            background: #0077ed;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 113, 227, 0.25);
        }

        .btn-multiply {
            background: #0071e3;
            color: white;
        }

        .btn-multiply:hover {
            background: #0077ed;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 113, 227, 0.25);
        }

        .btn-reset {
            background: #f5f5f7;
            color: #1d1d1f;
            grid-column: span 3;
        }

        .btn-reset:hover {
            background: #e8e8ed;
            transform: translateY(-1px);
        }

        .result {
            background: #f5f5f7;
            padding: 24px;
            border-radius: 12px;
            margin-top: 24px;
            text-align: center;
            min-height: 90px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
        }

        .result-label {
            color: #86868b;
            font-size: 13px;
            margin-bottom: 8px;
            font-weight: 500;
            letter-spacing: 0.2px;
        }

        .result-value {
            font-size: 36px;
            font-weight: 600;
            color: #1d1d1f;
            letter-spacing: -1px;
            transition: transform 0.2s ease;
        }

        .api-info {
            background: #f5f5f7;
            padding: 20px;
            margin-top: 32px;
            border-radius: 12px;
        }

        .api-info h3 {
            color: #1d1d1f;
            margin-bottom: 12px;
            font-size: 15px;
            font-weight: 600;
            letter-spacing: -0.2px;
        }

        .api-info code {
            background: white;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            color: #1d1d1f;
            font-family: 'SF Mono', Monaco, monospace;
        }

        .api-info p {
            color: #1d1d1f;
            font-size: 13px;
        }

        .footer {
            text-align: center;
            margin-top: 32px;
            color: #86868b;
            font-size: 12px;
            line-height: 1.6;
        }

        .error {
            color: #d60000;
            font-size: 13px;
            margin-top: 12px;
            display: none;
            font-weight: 500;
        }

        .loading {
            display: none;
            color: #0071e3;
            font-size: 13px;
            margin-top: 12px;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Calculator</h1>
        <div style="text-align: center;">
            <span class="status">Staging Environment</span>
        </div>

        <div class="calculator">
            <div class="input-group">
                <label for="num1">First Number</label>
                <input type="number" id="num1" placeholder="0">
            </div>

            <div class="input-group">
                <label for="num2">Second Number</label>
                <input type="number" id="num2" placeholder="0">
            </div>

            <div class="button-group">
                <button class="btn-add" onclick="calculate('add')">Add</button>
                <button class="btn-subtract" onclick="calculate('subtract')">Subtract</button>
                <button class="btn-multiply" onclick="calculate('multiply')">Multiply</button>
                <button class="btn-reset" onclick="reset()">Reset</button>
            </div>

            <div class="loading" id="loading">Calculating...</div>
            <div class="error" id="error"></div>

            <div class="result" id="result">
                <div class="result-label">Result</div>
                <div class="result-value" id="resultValue">-</div>
            </div>
        </div>

        <div class="api-info">
            <h3>API Endpoints</h3>
            <p style="margin: 5px 0;"><strong>Add:</strong> <code>GET /add?a={num1}&b={num2}</code></p>
            <p style="margin: 5px 0;"><strong>Subtract:</strong> <code>GET /subtract?a={num1}&b={num2}</code></p>
            <p style="margin: 5px 0;"><strong>Multiply:</strong> <code>GET /multiply?a={num1}&b={num2}</code></p>
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
        
        function reset() {
            const resultValue = document.getElementById('resultValue');
            const error = document.getElementById('error');
            const loading = document.getElementById('loading');

            // Reset input fields
            document.getElementById('num1').value = 0;
            document.getElementById('num2').value = 0;

            // Reset result display
            resultValue.textContent = 0;
            error.style.display = 'none';
            loading.style.display = 'none';
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


@app.get("/multiply")
async def api_multiply(a: float, b: float):
    """Multiply two numbers"""
    result = multiply(a, b)
    return {"operation": "multiply", "a": a, "b": b, "result": result}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "calculator-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
