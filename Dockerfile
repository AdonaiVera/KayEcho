# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any necessary dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for Cloud Run (8080)
EXPOSE 8080

# Set the environment variable PORT to 8080 for Cloud Run
ENV PORT 8080

# Run the Flask application
CMD ["python", "main.py"]
