FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt python-dotenv

# Copy .env file and application code
COPY .env .env
COPY . .

# Expose Flask default port
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
