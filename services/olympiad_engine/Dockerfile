# 2025-10-22: Dockerfile for Olympiad Engine Microservice
# Authors: Cascade

# 2025-10-22: Use an official Python runtime as a parent image
FROM python:3.9-slim

# 2025-10-22: Set the working directory in the container
WORKDIR /app

# 2025-10-22: Copy the dependencies file to the working directory
COPY requirements.txt .

# 2025-10-22: Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 2025-10-22: Copy the content of the local src directory to the working directory
COPY . .

# 2025-10-22: Make port 5005 available to the world outside this container
EXPOSE 5005

# 2025-10-22: Define environment variable
ENV NAME OlympiadEngine

# 2025-10-22: Run app.py when the container launches
CMD ["python", "app.py"]
