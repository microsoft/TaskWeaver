# CLI Only Mode

TaskWeaver's CLI-only mode enables users to effortlessly communicate with the Command Line Interface (CLI) using natural language. 
CodeInterpreter generates CLI commands, such as bash or PowerShell to address the user's needs. 
This allows users to operate your system by simply interacting with the command line through chat in natural language!

## Demo
TBD


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