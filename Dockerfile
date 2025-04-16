# -------- Builder Stage --------
    FROM python:3.11-slim as builder

    # Install system dependencies required for uv installation
    RUN apt-get update && \
        apt-get install -y --no-install-recommends curl build-essential && \
        rm -rf /var/lib/apt/lists/*
    
    # Install uv and ensure it's available in PATH
    RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
        ln -s /root/.local/bin/uv /usr/local/bin/uv
    
    WORKDIR /app
    
    # Copy requirements file and install dependencies using uv
    COPY requirements.txt .
    RUN uv pip install --system --no-cache-dir -r requirements.txt
    
    # Copy the entire project
    COPY . .
    
    # -------- Runtime Stage --------
    FROM python:3.11-slim as runtime
    
    # Install minimal runtime dependencies
    RUN apt-get update && \
        apt-get install -y --no-install-recommends curl && \
        rm -rf /var/lib/apt/lists/*
    
    # Install uv in the runtime stage (if needed for consistency)
    RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
        ln -s /root/.local/bin/uv /usr/local/bin/uv
    
    WORKDIR /app
    
    # Copy project files from the builder stage
    COPY --from=builder /app /app
    
    # Expose the application port (adjust if needed)
    EXPOSE 8000
    
    # Environment variables (if you want to set some defaults; additional variables come from --env-file)
    ENV PORT=8000 \
        BASE_URL="http://localhost:8000"
    
    # Run the FastAPI application using python as entrypoint
    CMD ["python", "app.py"]
    