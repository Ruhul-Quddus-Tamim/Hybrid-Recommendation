# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set environment variables to avoid Python buffering its output (helpful for logging)
ENV PYTHONUNBUFFERED 1

# Create a directory for the app code
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt /app/

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app code into the container
COPY . /app/

# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Expose the port the app runs on
EXPOSE 5001

# Command to run the app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]