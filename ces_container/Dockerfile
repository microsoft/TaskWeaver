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
COPY taskweaver/__init__.py /app/taskweaver/__init__.py
# Add the taskweaver directories to the PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/app/taskweaver"

CMD ["python", "/app/taskweaver/ces/docker_entry.py"]


