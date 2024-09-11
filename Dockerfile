# Use a specific Python version
FROM python:3.9

# Create a working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set environment variables for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=4242

# Expose the port the app will run on
EXPOSE 4242

# Run the Flask development server
CMD ["flask", "run"]

