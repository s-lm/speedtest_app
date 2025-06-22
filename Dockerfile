FROM python:3.12-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev postgresql-dev

# Copy app files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt
RUN mkdir -p /speedtest_app/conf
COPY speedtest_app /speedtest_app

# Expose port
EXPOSE 8080

# Run app
CMD ["gunicorn", "--env", "${PWD}/speedtest_app/conf/speedtest.cfg", "--bind", "0.0.0.0:8080", "--threads", "5", "--reuse-port", "--forwarded-allow-ips", "*", "speedtest_app:create_app()"]