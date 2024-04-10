FROM python:3.10-slim

RUN python3 -m pip install --upgrade pip

RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN useradd -m taskweaver
RUN chown taskweaver:taskweaver /app
USER taskweaver

COPY --chown=taskweaver:taskweaver requirements.txt .
RUN pip install --no-cache-dir --no-warn-script-location --user -r requirements.txt

RUN pip install --no-cache-dir --no-warn-script-location chainlit

# Define a build argument
ARG WITH_WEB_SEARCH=true

# Copy the model downloader script
COPY --chown=taskweaver:taskweaver docker/all_in_one_container/model_downloader.py .
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

COPY --chown=taskweaver:taskweaver taskweaver taskweaver
COPY --chown=taskweaver:taskweaver project project
COPY --chown=taskweaver:taskweaver docker/all_in_one_container/taskweaver_config.json project/taskweaver_config.json
COPY --chown=taskweaver:taskweaver playground playground

ENV EXECUTION_SERVICE_KERNEL_MODE="local"

# Install dependencies for different LLM models
RUN pip install --no-cache-dir --no-warn-script-location --user google-generativeai
RUN pip install --no-cache-dir --no-warn-script-location --user zhipuai
RUN pip install --no-cache-dir --no-warn-script-location --user dashscope


CMD ["sh", "-c", "python -m taskweaver -p ./project"]
