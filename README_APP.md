## Hello Bye Low Code App

A simple low code web application that displays "Hello" and "Bye" messages.

## Features

- Clean, modern web interface
- Three endpoints:
  - `/` - Main page with Hello and Bye messages
  - `/hello` - JSON endpoint returning Hello message
  - `/bye` - JSON endpoint returning Bye message

## Running the App

1. Make sure you have the dependencies installed:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn app:app --reload
```

3. Open your browser and visit:
- http://localhost:8000 - Main page
- http://localhost:8000/hello - Hello API endpoint
- http://localhost:8000/bye - Bye API endpoint

## API Documentation

FastAPI automatically generates interactive API documentation:
- http://localhost:8000/docs - Swagger UI
- http://localhost:8000/redoc - ReDoc
