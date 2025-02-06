# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for the webhook server (optional if using Flask with webhooks)
EXPOSE 3000

# Run the Flask app and Telegram bot when the container launches
CMD ["python", "bot.py"]
