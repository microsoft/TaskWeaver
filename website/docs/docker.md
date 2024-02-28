# Run TaskWeaver in Docker Container

In this document, we will show you how to use Docker container to run TaskWeaver.

## How to run TaskWeaver in Docker Container

1. Before you start, make sure you have Docker installed on your machine. If not, you can download it from [Docker's official website](https://www.docker.com/products/docker-desktop).
2. Open a terminal and run the following command to pull the TaskWeaver Docker image from Docker Hub:

```bash
docker pull taskweaver/taskweaver
```

3. Once the image is pulled, you can run the TaskWeaver container using the following command:

```bash
docker run -it -p 8000:8000 taskweaver/taskweaver
```
Then you can access the TaskWeaver Web UI by visiting [http://localhost:8000](http://localhost:8000) in your web browser. 

## How to configure configurations for TaskWeaver in Docker container
- Method 1: You can use environment variables to configure TaskWeaver. For example, you can use the following command to set the LLM configuration:

```bash
docker run -it -e LLM_API_BASE=<API_BASE> -e LLM_API_KEY=<API_KEY> -e LLM_API_TYPE=<API_TYPE> -e LLM_MODEL=<MODEL> -p 8000:8000 taskweaver/taskweaver
``` 
More details about how to set configurations via environment variables can be found in the [configurations](./configurations.md) document.

- Method 2: You can also mount your local `project` directory to the container. For example, you can use the following command:

```bash
 docker run -it -p 8000:8000 --mount  type=bind,source=<your_local_project_dir>,target=/app/TaskWeaver/project/  taskweaver/taskweaver
```
Then you can edit the `taskweaver_config.json` file in your local `project` directory to configure TaskWeaver.
In addition, you also can customize the plugins and examples in your local `project` directory.
The structure of the `project` directory can be referred to the `taskweaver/project` directory.