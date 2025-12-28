FROM python:3.13-slim
# Set working directory
WORKDIR /app

# Copy src code files
COPY requirements.txt .
COPY README.md .
COPY setup.py .
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir -e .

# Copy cookie file
COPY deploy/fantraxloggedin.cookie ./deploy/fantraxloggedin.cookie

# Default command - can be overridden
CMD ["python", "-m", "fantrax_service", "--cookie-path", "deploy/fantraxloggedin.cookie"]
