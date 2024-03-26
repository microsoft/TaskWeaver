FROM python:3.10-slim

ENV EXECUTION_SERVICE_KERNEL_MODE="local"

WORKDIR /app

RUN python3 -m pip install --upgrade pip

RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/microsoft/TaskWeaver.git
RUN cd TaskWeaver && pip install -r requirements.txt

RUN pip install chainlit

EXPOSE 8000

CMD ["sh", "-c", "cd TaskWeaver && python -m taskweaver -p ./project"]
