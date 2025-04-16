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
    
    # Copy requirements file
    COPY requirements.txt .
    
    # Install dependencies using uv
    RUN uv pip install --system --no-cache-dir -r requirements.txt
    
    # Explicitly install uvicorn (in case it's missing from requirements.txt)
    RUN pip install --no-cache-dir uvicorn
    RUN pip install --no-cache-dir huggingface_hub[hf_xet]
    RUN pip install --no-cache-dir python-dotenv
    
    # Copy the entire project
    COPY . .
    
    # -------- Runtime Stage --------
    FROM python:3.11-slim as runtime
    
    # Install minimal runtime dependencies
    RUN apt-get update && \
        apt-get install -y --no-install-recommends curl && \
        rm -rf /var/lib/apt/lists/*
    
    # Explicitly install uvicorn in the runtime container
    RUN pip install --no-cache-dir uvicorn
    
    WORKDIR /app
    
    # Copy project files from the builder stage
    COPY --from=builder /app /app
    COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
    
    # Expose the application port (adjust if needed)
    EXPOSE 8000
    
    # Environment variables
    ENV PORT=8000 \
        BASE_URL="http://localhost:8000" \
        PYTHONPATH=/app
    
    # Run the FastAPI application using python as entrypoint
    CMD ["python", "app.py"]
