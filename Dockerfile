FROM python:3.13-slim
# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
COPY README.md .
RUN pip install --no-cache-dir -r requirements.txt

# Copy setup.py and install the package
COPY setup.py .
COPY src/ ./src/
RUN pip install --no-cache-dir -e .

# Copy deploy directory (for cookie files)
COPY deploy/ ./deploy/

# Set environment variables for Chrome
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/google-chrome

# Default command - can be overridden
CMD ["python", "-m", "fantrax_service"]

