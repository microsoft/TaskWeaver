FROM python:3.10-slim

RUN python3 -m pip install --upgrade pip

RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --no-warn-script-location -r requirements.txt

RUN pip install --no-cache-dir --no-warn-script-location chainlit

# Define a build argument
ARG WITH_WEB_SEARCH=true

# Copy the model downloader script
COPY docker/all_in_one_container/model_downloader.py .
# Install the web search dependencies
RUN if [ "$WITH_WEB_SEARCH" = "true" ]; then \
    pip install --no-cache-dir --no-warn-script-location "duckduckgo_search>=5.1.0" \
    "langchain>=0.1.4" \
    "langchain-community>=0.0.16" \
    "beautifulsoup4>=4.12.2" \
    "html2text>=2020.1.16" \
    "faiss-cpu>=1.8.0" \
    "sentence-transformers>=2.6.0"; \
    python model_downloader.py; \
    fi

COPY taskweaver taskweaver
COPY project project
COPY docker/all_in_one_container/taskweaver_config.json project/taskweaver_config.json
COPY docker/all_in_one_container/entrypoint.sh entrypoint.sh
RUN chmod +x entrypoint.sh
COPY docker/all_in_one_container/entrypoint_chainlit.sh entrypoint_chainlit.sh
RUN chmod +x entrypoint_chainlit.sh
COPY playground playground

ENV EXECUTION_SERVICE_KERNEL_MODE="local"

# Install dependencies for different LLM models
RUN pip install --no-cache-dir --no-warn-script-location google-generativeai
RUN pip install --no-cache-dir --no-warn-script-location zhipuai
RUN pip install --no-cache-dir --no-warn-script-location dashscope

ENTRYPOINT ["/app/entrypoint.sh"]


