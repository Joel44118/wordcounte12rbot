# Use a lightweight official Python image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the bot code
COPY bot.py .

# Expose the port the app runs on
EXPOSE 8080

# Command to run the bot
CMD ["python", "bot.py"]
