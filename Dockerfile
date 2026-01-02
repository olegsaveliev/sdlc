# This is like a recipe for your app
# Start with Python 3.10 (like starting with a clean kitchen)
FROM python:3.10-slim

# Set the working folder inside the container
WORKDIR /app

# Copy requirements.txt first (if it exists)
COPY requirements.txt* ./

# Install Python packages (if requirements.txt exists)
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copy all your code files
COPY . .

# Tell Docker your app listens on port 8000
EXPOSE 8000

# Start your app when the container runs
# This creates a simple web server so QA can access it
CMD python3 -c "import http.server; import socketserver; PORT = 8000; Handler = http.server.SimpleHTTPRequestHandler; httpd = socketserver.TCPServer(('', PORT), Handler); print(f'Server running on port {PORT}'); httpd.serve_forever()"
