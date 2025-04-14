# Use an official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy required files
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose port
EXPOSE 5000

# Command to run the app
CMD ["python", "app.py"]