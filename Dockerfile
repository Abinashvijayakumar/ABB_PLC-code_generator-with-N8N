# Use a specific, slim version of Python for a smaller, faster image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the file that lists our Python dependencies
COPY requirements.txt .

# Install the dependencies
# --no-cache-dir makes the image smaller
# --trusted-host is sometimes needed in corporate networks or CI/CD environments
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

# Copy the entire backend directory into the container
COPY ./backend /app/backend

# Copy the RAG knowledge base directory into the container
# This is for the initial build. The volume will override this for live updates.
COPY ./rag_kb /app/rag_kb

# Copy the .env file for the API key
COPY .env .

# Expose the port that the main orchestrator will run on
EXPOSE 8000
