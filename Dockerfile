# Use an official Python image as the base image
FROM python:3.9-slim

# Set the working directory in the container (optional, if you want to keep the root directory)
WORKDIR /

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container
COPY . /

RUN pip cache purge

# Install required Python packages
RUN pip install --no-cache-dir --timeout=3000 --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

# Expose the port your app runs on
EXPOSE 8080 

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--threads", "2", "--timeout", "3000", "main:app"]

