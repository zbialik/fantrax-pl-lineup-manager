FROM python:3.13-slim
# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
COPY README.md .
COPY setup.py .
COPY src/ ./src/
COPY deploy/ ./deploy/
RUN pip install --no-cache-dir -e .

# Default command - can be overridden
CMD ["python", "-m", "fantrax_pl_lineup_manager"]

