# Use the official Python 3.10 image as the base image  
FROM python:3.10

# Set the working directory to /app
WORKDIR /app

# Copy the requrements file
COPY requirements.txt /app/requirements.txt

# Install any necessary dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project code
COPY taskweaver/ces /app/taskweaver/ces
COPY taskweaver/plugin /app/taskweaver/plugin
COPY taskweaver/module /app/taskweaver/module
COPY taskweaver/__init__.py /app/taskweaver/__init__.py
COPY docker_entry.py /app/docker_entry.py

ENV PYTHONPATH "${PYTHONPATH}:/app"

CMD ["python", "docker_entry.py"]


