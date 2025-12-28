from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with Hello and Bye messages"""
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Hello Bye App</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }
                .container {
                    text-align: center;
                    background: white;
                    padding: 50px;
                    border-radius: 20px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                }
                h1 {
                    color: #667eea;
                    font-size: 48px;
                    margin: 20px 0;
                }
                .message {
                    font-size: 32px;
                    color: #764ba2;
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="message">👋 Hello!</div>
                <h1>Welcome to the App</h1>
                <div class="message">👋 Bye!</div>
            </div>
        </body>
    </html>
    """
    return html_content

@app.get("/hello")
async def hello():
    """Hello endpoint"""
    return {"message": "Hello!"}

@app.get("/bye")
async def bye():
    """Bye endpoint"""
    return {"message": "Bye!"}
