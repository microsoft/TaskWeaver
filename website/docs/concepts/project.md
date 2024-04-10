# Project

A project folder is a directory that stores the configuration files, plugins, examples, logs, and workspace data.
A TaskWeaverApp instance is associated with a project folder. The project folder is created by the user and contains all the necessary files and folders for the TaskWeaverApp to run.

The following is a typical project directory structure:
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

The `workspace` folder stores the session data, which includes the code execution service (CES) folder and the current working directory (CWD) folder.
Therefore, if the code execution results in any files, they will be stored in the CWD folder.
If you are running in `local` mode and want to load files from your local file system, the CWD is the base directory to load the files from.