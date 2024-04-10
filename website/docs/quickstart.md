# Quick Start

## Installation
You can install TaskWeaver by running the following command:
```bash
# [optional] create a conda environment to isolate the dependencies
# conda create -n taskweaver python=3.10
# conda activate taskweaver

# clone the repository
git clone https://github.com/microsoft/TaskWeaver.git
cd TaskWeaver
# install the requirements
pip install -r requirements.txt
```


## Project Directory
TaskWeaver runs as a process, you need to create a project directory to store plugins and configuration files. 
We provided a sample project directory in the `project` folder. You can copy the `project` folder to your workspace.
A project directory typically contains the following files and folders:

```bash
📦project
 ┣ 📜taskweaver_config.json # the project configuration file for TaskWeaver
 ┣ 📂plugins # the folder to store plugins
 ┣ 📂planner_examples # the folder to store planner examples
 ┣ 📂codeinterpreter_examples # the folder to store code interpreter examples
 ┣ 📂logs # the folder to store logs, will be generated after program starts
 ┗ 📂workspace # the directory stores session data， will be generated after program starts
    ┗ 📂 session_id 
      ┣ 📂ces # the folder used by the code execution service
      ┣ 📂cwd # the current working directory to run the generated code
      ┗ other session data
```

## OpenAI Configuration
Before running TaskWeaver, you need to provide your OpenAI API key and other necessary information. 
You can do this by editing the `taskweaver_config.json` file. 
If you are using Azure OpenAI, you need to set the following parameters in the `taskweaver_config.json` file:
### Azure OpenAI
```json
{
"llm.api_base": "https://xxx.openai.azure.com/",
"llm.api_key": "your_api_key",
"llm.api_type": "azure",
"llm.api_version": "the api version",
"llm.model": "the model name, e.g., gpt-4" # In Azure OpenAI, the model name is the deployment_name
}
```

### OpenAI
```json
{
"llm.api_key": "the api key",
"llm.model": "the model name, e.g., gpt-4"
}
```
>💡 Only the latest OpenAI API supports the `json_object` response format. 
> If you are using an older version of OpenAI API, you need to set the `"llm.response_format"`=`null` in the `taskweaver_config.json` file.

More configuration options can be found in the [configuration documentation](./configurations/overview).

## Start TaskWeaver
```bash
# assume you are in the TaskWeaver folder cloned from the repository
python -m taskweaver -p ./project/ # -p is the path to the project directory
```
This will start the TaskWeaver process and you can interact with it through the command line (CLI) interface. 
If everything goes well, you will see the following prompt:

```bash
=========================================================
 _____         _     _       __
|_   _|_ _ ___| | _ | |     / /__  ____ __   _____  _____
  | |/ _` / __| |/ /| | /| / / _ \/ __ `/ | / / _ \/ ___/
  | | (_| \__ \   < | |/ |/ /  __/ /_/ /| |/ /  __/ /
  |_|\__,_|___/_|\_\|__/|__/\___/\__,_/ |___/\___/_/
=========================================================
TaskWeaver: I am TaskWeaver, an AI assistant. To get started, could you please enter your request?
Human: ___
```

There are other ways to start TaskWeaver:
- [A Chainlit UI interface](./usage/webui.md): TaskWeaver provides an experimental web-based interface to interact with the system.
- [A Library](./usage/library.md): You can also use TaskWeaver as a library in your Python code.
- [The all-in-one Docker image](./usage/docker.md): We provide a Docker image that contains all the dependencies to run TaskWeaver.
