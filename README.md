<h1 align="center">
    <img src="./.asset/logo.color.svg" width="45" /> TaskWeaver
</h1>

A **code-first** agent framework for seamlessly planning and executing data analytics tasks. 
This innovative framework interprets user requests through coded snippets and efficiently 
coordinates a variety of plugins in the form of functions to execute 
data analytics tasks

**Highlighted Features**

- [x] **Rich data structure** - TaskWeaver allows you to work with rich data 
    structures in Python, such as DataFrames, instead of having to work with 
    text strings.
- [x] **Customized algorithms** - TaskWeaver allows you to encapsulate your 
    own algorithms into plugins (in the form of Python functions), 
    and orchestrate them to achieve complex tasks.
- [x] **Incorporating domain-specific knowledge** - TaskWeaver is designed to 
    be easily incorporating domain-specific knowledge, such as the knowledge 
    of execution flow, to improve the reliability of the AI copilot.
- [x] **Stateful conversation** - TaskWeaver is designed to support stateful 
    conversation. It can remember the context of the conversation and 
    leverage it to improve the user experience.
- [x] **Code verification** - TaskWeaver is designed to verify the generated code 
    before execution. It can detect potential issues in the generated code 
    and provide suggestions to fix them.
- [x] **Easy to use** - TaskWeaver is designed to be easy to use. 
    We provide a set of sample plugins and a tutorial to help you get started.
    Users can easily create their own plugins based on the sample plugins.
    TaskWeaver offers an open-box experience, allowing users to run a service immediately after installation.
- [x] **Easy to debug** - TaskWeaver is designed to be easy to debug. 
    We have detailed logs to help you understand what is going on during calling the LLM, 
    the code generation, and execution process.
- [x] **Security consideration** - TaskWeaver supports a basic session management to keep
    different users' data separate. The code execution is separated into different processes in order not to interfere with each other.
- [x] **Easy extension** - TaskWeaver is designed to be easily extended to accomplish 
    more complex tasks. You can create multiple AI copilots to
    act in different roles, and orchestrate them to achieve complex tasks.

# News

- [2023-12-12] A simple UI demo is available in playground/UI folder, try with the [README](/playground/UI/README.md)
- [2023-11-30] TaskWeaver is released on GitHub🎈. 


# Getting started

## Prerequisites

- Python 3.10 or above
- OpenAI (or Azure OpenAI) access with GPT-3.5 above models. However, it is strongly recommended to use the GPT-4, which is more stable.
- Other requirements can be found in the `requirements.txt` file. 

> OpenAI API had a major [update](https://github.com/openai/openai-python) from 0.xx to 1.xx in November 2023. 
> Please make sure you are not using an old version because the API is not backward compatible.


## Quick Start

### Installation
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


### Project Directory
TaskWeaver runs as a process, you need to create a project directory to store plugins and configuration files. 
We provided a sample project directory in the `project` folder. You can copy the `project` folder to your workspace.
A project directory typically contains the following files and folders:

```bash
📦project
 ┣ 📜taskweaver_config.json # the configuration file for TaskWeaver
 ┣ 📂plugins # the folder to store plugins
 ┣ 📂planner_examples # the folder to store planner examples
 ┣ 📂codeinterpreter_examples # the folder to store code interpreter examples
 ┣ 📂sample_data # the folder to store sample data used for evaluations
 ┣ 📂logs # the folder to store logs, will be generated after program starts
 ┗ 📂workspace # the directory stores session data， will be generated after program starts
    ┗ 📂 session_id 
      ┣ 📂ces # the folder used by the code execution service
      ┗ 📂cwd # the current working directory to run the generated code
```

### OpenAI Configuration
Before running TaskWeaver, you need to provide your OpenAI API key and other necessary information. 
You can do this by editing the `taskweaver_config.json` file. 
If you are using Azure OpenAI, you need to set the following parameters in the `taskweaver_config.json` file:
#### Azure OpenAI
```json
{
"llm.api_base": "https://xxx.openai.azure.com/",
"llm.api_key": "your_api_key",
"llm.api_type": "azure",
"llm.api_version": "the api version",
"llm.model": "the model name, e.g., gpt-4"
}
```

#### OpenAI
```json
{
"llm.api_key": "the api key",
"llm.model": "the model name, e.g., gpt-4"
}
```
>💡 Only the latest OpenAI API supports the `json_object` response format. 
> If you are using an older version of OpenAI API, you need to set the `llm.response_format` to `null`.

More configuration options can be found in the [configuration documentation](docs/configuration.md).

### Start TaskWeaver
```bash
# assume you are in the taskweaver folder
# -p is the path to the project directory
python -m taskweaver -p ./project/
```
This will start the TaskWeaver process and you can interact with it through the command line interface. 
If everything goes well, you will see the following prompt:

```
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

### Two Walkthrough Examples



#### Example 1: Pull data from a database and apply an anomaly detection algorithm
In this example, we will show you how to use TaskWeaver to pull data from a database and apply an anomaly detection algorithm.

[Anomaly Detection](https://github.com/microsoft/TaskWeaver/assets/7489260/9f854acf-f2bf-4566-9d16-f84e915d0f4e)

If you want to follow this example, you need to configure the `sql_pull_data` plugin in the `project/plugins/sql_pull_data.yaml` file.
You need to provide the following information:
```yaml
api_type: azure or openai
api_base: ...
api_key: ...
api_version: ...
deployment_name: ...
sqlite_db_path: sqlite:///../../../sample_data/anomaly_detection.db
```
The `sql_pull_data` plugin is a plugin that pulls data from a database. It takes a natural language request as input and returns a DataFrame as output.

This plugin is implemented based on [Langchain](https://www.langchain.com/).
If you want to follow this example, you need to install the Langchain package:
```bash
pip install langchain
pip install tabulate
```

#### Example 2: Forecast QQQ's price in the next week
In this example, we will show you how to use TaskWeaver to forecast QQQ's price in the next week using the ARIMA algorithm. 

[Nasdaq 100 Index Price Forecasting](https://github.com/microsoft/TaskWeaver/assets/7489260/c2b09615-52d8-491f-bbbf-e86ba282e59a)

If you want to follow this example, you need to you have two requirements installed:
```bash
pip install yfinance
pip install statsmodels
```

For more examples, please refer to our [paper](http://export.arxiv.org/abs/2311.17541). 

> 💡 The planning of TaskWeaver are based on the LLM model. Therefore, if you want to repeat the examples, the execution process may be different
> from what you see in the videos. Typically, more concrete prompts will help the model to generate better plans and code.

## How to use TaskWeaver in your project

### Using TaskWeaver as a library
After cloning the TaskWeaver repository, you can install TaskWeaver as a library by running the following command:
```bash
# clone the repository
cd TaskWeaver
pip install -e .
```
Then, you can follow the [documentation](docs/taskweaver_as_a_lib.md) to use TaskWeaver in your code.

### Using TaskWeaver as a service
TaskWeaver can be used as a service that can be called by other programs. More details are TBD.

## Customizing TaskWeaver

There are two ways to customize TaskWeaver: creating plugins and creating examples. 

### Creating Plugins

Since TaskWeaver can already perform some basic tasks, you can create plugins to extend its capabilities.
A plugin is a python function that takes a set of arguments and returns a set of results.

Typically, you only need to write a plugin in the following example scenarios:
- You want to encapsulate your own algorithm into a plugin.
- You want to import a python package that is not supported by TaskWeaver.
- You want to connect to an external data source to pull data.
- You want to query a web API.

Refer to the [plugin documentation](docs/plugin.md) for more details. Otherwise, you can leverage TaskWeaver's code generation capability to perform tasks.

### Creating Examples

The purpose of examples is to help LLMs understand how to perform tasks especially when 
the tasks are complex and need domain-specific knowledge.

There are two types of examples: (1) planning examples and (2) code interpreter examples.
Planning examples are used to demonstrate how to use TaskWeaver to plan for a specific task.
Code generation examples are used to demonstrate how to generate code or orchestrate plugins to perform a specific task.

Refer to the [example documentation](docs/example.md) for more details.

## Citation
Our paper could be found [here](http://export.arxiv.org/abs/2311.17541). 
If you use TaskWeaver in your research, please cite our paper:
```
@article{taskweaver,
  title={TaskWeaver: A Code-First Agent Framework},
  author={Bo Qiao, Liqun Li, Xu Zhang, Shilin He, Yu Kang, Chaoyun Zhang, Fangkai Yang, Hang Dong, Jue Zhang, Lu Wang, Minghua Ma, Pu Zhao, Si Qin, Xiaoting Qin, Chao Du, Yong Xu, Qingwei Lin, Saravan Rajmohan, Dongmei Zhang},
  journal={arXiv preprint arXiv:2311.17541},
  year={2023}
}
```


## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
