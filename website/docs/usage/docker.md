# All-in-One Docker Image

In this document, we will show you how to run TaskWeaver using the All-in-One Docker Image.
Please note that the All-in-One Docker Image is for development and testing purposes only.

## Prerequisites
You need to have Docker installed on your machine. 

For Windows and macOS users, you can use Docker Desktop. You can download it from [Docker's official website](https://www.docker.com/products/docker-desktop).

For Linux users, you can install following the instructions in the [Docker's official website](https://docs.docker.com/engine/install/). 
Please find the installation guide for your specific Linux distribution.

## Run TaskWeaver using the All-in-One Docker Image

There are two versions of the TaskWeaver All-in-One Docker Image:
- `taskweavercontainers/taskweaver-all-in-one:latest`: This version includes the Planner and CodeInterpreter roles only.
You can use this container for code generation and execution tasks.
- `taskweavercontainers/taskweaver-all-in-one:latest-ws`: This version includes an additional WebSearch role which can search the web for information. 
As it requires dependencies to the `sentence-transformers` library, it is larger.

Open a terminal and run the following command to obtain the TaskWeaver image:

```bash
docker pull taskweavercontainers/taskweaver-all-in-one:latest
# if you want to use the version with the WebSearch role 
# docker pull taskweavercontainers/taskweaver-all-in-one:latest-ws
```

Once the image is pulled, you can run the TaskWeaver container using the following command:

```bash
docker run -it -e LLM_API_BASE=<API_BASE> \
  -e LLM_API_KEY=<API_KEY> \
  -e LLM_API_TYPE=<API_TYPE> \
  -e LLM_MODEL=<MODEL> \
  taskweavercontainers/taskweaver-all-in-one:latest
```

If you want to run TaskWeaver in UI mode, you can use the following command:

```bash
docker run -it -e LLM_API_BASE=<API_BASE> \
  -e LLM_API_KEY=<API_KEY> \
  -e LLM_API_TYPE=<API_TYPE> \
  -e LLM_MODEL=<MODEL> \
  -p 8000:8000 \
  --entrypoint /app/entrypoint_chainlit.sh \
  taskweavercontainers/taskweaver-all-in-one:latest 
```
Then you can access the TaskWeaver Web UI by visiting [http://localhost:8000](http://localhost:8000) in your web browser.

## How to run TaskWeaver on your own project directory
You can mount your local `project` directory to the container. For example, you can use the following command:

```bash
docker run -it -e LLM_API_BASE=<API_BASE> \
  -e LLM_API_KEY=<API_KEY> \
  -e LLM_API_TYPE=<API_TYPE> \
  -e LLM_MODEL=<MODEL> \
#  -e TASKWEAVER_UID=$(id -u) \ # uncomment if your host OS is not Windows
#  -e TASKWEAVER_GID=$(id -g) \ # uncomment if your host OS is not Windows
  --mount type=bind,source=<your_local_project_dir>,target=/app/TaskWeaver/project/ \
  taskweavercontainers/taskweaver-all-in-one:latest
```
Then you can edit the `taskweaver_config.json` file in your local `project` directory to configure TaskWeaver.
In addition, you also can customize the plugins and examples in your local `project` directory.
The structure of the `project` directory can be referred to the `taskweaver/project` directory.

## How to access your local files in the container
You can mount your local directory to the container. For example, you can use the following command:

```bash
docker run -it -e LLM_API_BASE=<API_BASE> \
  -e LLM_API_KEY=<API_KEY> \
  -e LLM_API_TYPE=<API_TYPE> \
  -e LLM_MODEL=<MODEL> \
#  -e TASKWEAVER_UID=$(id -u) \ # uncomment if your host OS is not Windows
#  -e TASKWEAVER_GID=$(id -g) \ # uncomment if your host OS is not Windows
  --mount type=bind,source=<your_local_dir>,target=/app/TaskWeaver/local/ \
  taskweavercontainers/taskweaver-all-in-one:latest
```

Then you can access your local files in the container by visiting the `/app/TaskWeaver/local/` directory.
You can load a file under the `/app/TaskWeaver/local/` directory in the TaskWeaver CLI 
with the `/load` command. For example, you can load a file named `example.csv` by running the following command:

```bash
 TaskWeaver ▶  I am TaskWeaver, an AI assistant. To get started, could you please enter your request?
    Human   ▶  /load /app/TaskWeaver/local/example.csv
    Human   ▶  display the column names of the loaded file
```