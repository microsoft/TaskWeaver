# Use the official Python 3.10 image as the base image  
FROM python:3.10-slim

WORKDIR /app

RUN groupadd --gid 10002 taskweaver
RUN useradd --uid 10002 --gid taskweaver -m taskweaver

# Set the working directory to /app
RUN chown taskweaver:taskweaver /app

USER taskweaver

# Copy the requrements file
COPY --chown=taskweaver:taskweaver requirements.txt .
RUN pip install --no-cache-dir --no-warn-script-location --user -r requirements.txt

# TODO: Install additional packages for plugins

# Copy the project code
COPY --chown=taskweaver:taskweaver taskweaver/ces /app/taskweaver/ces
COPY --chown=taskweaver:taskweaver taskweaver/plugin /app/taskweaver/plugin
COPY --chown=taskweaver:taskweaver taskweaver/module /app/taskweaver/module
COPY --chown=taskweaver:taskweaver taskweaver/__init__.py /app/taskweaver/__init__.py

ENV PYTHONPATH "${PYTHONPATH}:/app"

CMD ["python", "-m", "taskweaver.ces.kernel.launcher"]


