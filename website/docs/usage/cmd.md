# Terminal

This is the command line interface for TaskWeaver. You can interact with TaskWeaver through this interface.

Follow the instruction in [Quick Start](../quickstart.md) to clone the repository and fill in the necessary configurations.

Run the following command in terminal.
```bash
# assume you are in the TaskWeaver folder
python -m taskweaver -p ./project/ # -p is the path to the project directory
```
This will start the TaskWeaver process, and you can interact with it through the command line interface. 
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

We have provided a set of commands to interact with TaskWeaver. You can type `help` to see the list of available commands.
All commands start with a `/` character. For example, you can type `/help` to see the list of available commands.

```bash
 TaskWeaver ▶  I am TaskWeaver, an AI assistant. To get started, could you please enter your request?
    Human   ▶  /help

TaskWeaver Chat Console
-----------------------
/load <file>: load a file
/info: print the information of the current session
/reset: reset the session
/clear: clear the console
/exit: exit the chat console
/help: print this help message
/save: save the chat history of the current session for experience extraction
```

The table of commands supported by TaskWeaver is as follows:

| Command        | Description                                                               |
|----------------|---------------------------------------------------------------------------|
| `/load <file>` | Load a file by its absolute path, e.g., /load /home/taskweaver/sample.csv |
| `/info`        | Print the session id and the active roles of the current session          |
| `/reset`       | Reset the current session and start a new session                         |
| `/clear`       | Clear the console content                                                 |
| `/exit`        | Exit the chat console                                                     |
| `/help`        | Print the help message                                                    |
| `/save`        | Save the chat history of the current session for experience extraction    |

:::tip
When TaskWeaver runs generated code, the CWD (current working directory) is set to the `project/workspace/session_id/cwd` directory.
If you need to use relative paths in the generated code, the `cwd` directory should be the base path.
:::