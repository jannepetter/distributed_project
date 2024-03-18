FROM python:3.9

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY loadb.py .
RUN pip install Flask requests

# Expose port
EXPOSE 9000

# Command to run the load balancer
CMD ["python3", "loadb.py"]