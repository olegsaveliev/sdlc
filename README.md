# Calculator API

A professional, production-ready calculator API built with FastAPI, featuring a modern web interface and RESTful API endpoints.

## Features

- **RESTful API**: Four basic arithmetic operations (add, subtract, multiply, divide)
- **Web Interface**: Beautiful, responsive calculator UI with animations
- **Type Safety**: Full type hints and Pydantic validation
- **Configuration Management**: Environment-based configuration
- **Testing**: Comprehensive unit and integration tests
- **Docker Support**: Ready for containerized deployment

## Project Structure

```
sdlc/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py               # Configuration management
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # API route handlers
│   ├── services/
│   │   ├── __init__.py
│   │   └── calculator.py       # Business logic (calculator operations)
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic request/response models
│   ├── templates/
│   │   └── index.html          # Jinja2 HTML template
│   └── static/
│       ├── css/
│       │   └── style.css       # CSS styles
│       └── js/
│           └── calculator.js   # JavaScript functionality
├── tests/
│   ├── __init__.py
│   ├── test_calculator.py      # Unit tests for calculator service
│   └── test_api.py             # API integration tests
├── .env.example                 # Environment variables template
├── Dockerfile                   # Docker configuration
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Setup

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository** (if applicable):
   ```bash
   git clone <repository-url>
   cd sdlc
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

## Configuration

The application uses environment variables for configuration. Create a `.env` file in the root directory or set environment variables:

```env
# API Configuration
API_TITLE=Calculator API
API_VERSION=1.0.0
ENVIRONMENT=Staging
SERVICE_NAME=calculator-api

# Server Configuration
HOST=0.0.0.0
PORT=80

# Debug
DEBUG=false
```

### Environment Variables

- `API_TITLE`: Title of the API (default: "Calculator API")
- `API_VERSION`: API version (default: "1.0.0")
- `ENVIRONMENT`: Environment name - Staging, Production, Development (default: "Staging")
- `SERVICE_NAME`: Service identifier (default: "calculator-api")
- `HOST`: Server host (default: "0.0.0.0")
- `PORT`: Server port (default: 80)
- `DEBUG`: Enable debug mode (default: false)

## Running the Application

### Development Mode

```bash
python -m app.main
```

Or using uvicorn directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 80
```

The application will be available at:
- Web Interface: http://localhost:8000/
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## API Endpoints

### Web Interface
- `GET /` - Calculator web interface

### Calculator Operations
- `GET /add?a={num1}&b={num2}` - Add two numbers
- `GET /subtract?a={num1}&b={num2}` - Subtract two numbers
- `GET /multiply?a={num1}&b={num2}` - Multiply two numbers
- `GET /divide?a={num1}&b={num2}` - Divide two numbers

### System
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

### Example API Request

```bash
curl "http://localhost:8000/add?a=10&b=5"
```

Response:
```json
{
  "operation": "add",
  "a": 10.0,
  "b": 5.0,
  "result": 15.0
}
```

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app --cov-report=html
```

## Docker Deployment

### Build the Docker image:

```bash
docker build -t calculator-api .
```

### Run the container:

```bash
docker run -p 80:80 calculator-api
```

The application will be available at http://localhost:80

### Docker with environment variables:

```bash
docker run -p 80:80 -e ENVIRONMENT=Production -e PORT=80 calculator-api
```

## Architecture

The application follows a clean architecture pattern with clear separation of concerns:

1. **Services Layer** (`app/services/`): Contains business logic
2. **API Layer** (`app/api/`): Handles HTTP requests and responses
3. **Models Layer** (`app/models/`): Defines data schemas and validation
4. **Configuration** (`app/config.py`): Centralized configuration management
5. **Templates & Static** (`app/templates/`, `app/static/`): Frontend assets

## Development

### Adding New Features

1. **New Calculator Operation**: Add method to `app/services/calculator.py`
2. **New API Endpoint**: Add route to `app/api/routes.py`
3. **New Schema**: Add model to `app/models/schemas.py`

### Code Style

The project follows PEP 8 style guidelines. Consider using:
- `black` for code formatting
- `flake8` for linting
- `mypy` for type checking

## Security

**Important**: This project follows security best practices:

- ✅ No hardcoded secrets or credentials
- ✅ All sensitive data via environment variables
- ✅ `.env` file excluded from version control
- ✅ Docker images run as non-root user
- ✅ Health checks enabled

### Before Committing

1. **Never commit** `.env` files or secrets
2. Use `.env.example` as a template
3. Review `SECURITY.md` for detailed guidelines
4. Run the pre-commit checklist in `PRE_COMMIT_CHECKLIST.md`

### AWS Deployment

For AWS deployment, use:
- **ECS Task Definition** environment variables
- **AWS Secrets Manager** for sensitive data
- **GitHub Secrets** for CI/CD pipelines

See `SECURITY.md` for complete security guidelines.

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Security

If you discover a security vulnerability, please report it privately. See `SECURITY.md` for details.
