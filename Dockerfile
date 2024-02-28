FROM python:3.11-rc-slim

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

CMD ["sh", "-c", "cd TaskWeaver/playground/UI/ && chainlit run --host 0.0.0.0 --port 8000 app.py"]
