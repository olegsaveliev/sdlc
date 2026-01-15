"""FastAPI application initialization."""

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

from app.api import routes
from app.config import settings

# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="A professional calculator API with web interface",
)

# Get the base directory (app/)
BASE_DIR = Path(__file__).parent

# Setup Jinja2 templates
templates_dir = BASE_DIR / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(templates_dir)))


# Add url_for function to Jinja2 environment for static files
def url_for_static(path: str) -> str:
    """Generate URL for static files."""
    return f"/static{path}"


jinja_env.globals["url_for"] = url_for_static


# Mount static files
static_dir = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Dependency to get template
def get_template(name: str):
    """Get a Jinja2 template by name."""
    return jinja_env.get_template(name)


# Update the root route to use the template dependency
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Serve the HTML calculator interface.

    Returns:
        HTMLResponse: The calculator web interface
    """
    template = get_template("index.html")
    html_content = template.render(
        title=settings.api_title,
        environment=settings.environment,
        request=request,
    )
    return html_content


# Include API routes
app.include_router(routes.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
