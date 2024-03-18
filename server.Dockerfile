FROM python:3.9

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY server.py .
RUN pip install Flask requests

CMD ["python3", "server.py"]