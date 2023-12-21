# Terminal

1. Follow the instruction in [Quick Start](../quickstart.md) to clone the repo and make configurations

```bash
git clone https://github.com/microsoft/TaskWeaver.git
cd TaskWeaver
# install the requirements
pip install -r requirements.txt
```

```json
{
"llm.api_key": "the api key",
"llm.model": "the model name, e.g., gpt-4"
}
```

2. Run the following command in terminal.
```bash
# assume you are in the taskweaver folder
# -p is the path to the project directory
python -m taskweaver -p ./project/
```
This will start the TaskWeaver process and you can interact with it through the command line interface. 
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
