# Use the official Python 3.10 image as the base image  
FROM python:3.10-slim

WORKDIR /app

# Copy the requrements file
COPY requirements.txt .
RUN pip install --no-cache-dir --no-warn-script-location -r requirements.txt

# TODO: Install additional packages for plugins

# Copy the project code
COPY taskweaver/ces /app/taskweaver/ces
COPY taskweaver/plugin /app/taskweaver/plugin
COPY taskweaver/module /app/taskweaver/module
COPY taskweaver/__init__.py /app/taskweaver/__init__.py
COPY docker/ces_container/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENV PYTHONPATH="/app"

ENTRYPOINT ["/app/entrypoint.sh"]


