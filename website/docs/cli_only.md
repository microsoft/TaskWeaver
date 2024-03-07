# CLI Only Mode

TaskWeaver's CLI-only mode enables users to effortlessly communicate with the Command Line Interface (CLI) using natural language. 
CodeInterpreter generates CLI commands, such as bash or PowerShell to address the user's needs.
This mode allows users to operate your system by simply chatting with the command line in natural language!


## Demo

[TaskWeaver-CLI](https://github.com/microsoft/TaskWeaver/assets/32928431/3724d321-0e0b-49e0-8f77-7b3855069a82)


## How to enable
Just add the following configuration to the project configuration file `taskweaver_config.json`:
```json
{
  "session.code_interpreter_only": true,
  "session.code_gen_mode": "cli_only"
}
```
Please refer to the [session](./session.md) documentation for more details.

Note: It is better to enable `session.code_interpreter_only` when CLI only mode is enabled.
