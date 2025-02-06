# Use Python's official image as a base
FROM python:3.9-slim

# Set working directory inside the container
WORKDIR /app

# Copy the requirements.txt into the container
COPY requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY bot.py /app/

# Expose the health check port (8000)
EXPOSE 8000

# Command to run the bot
CMD ["python", "bot.py"]
