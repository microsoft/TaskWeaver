# Demo

[Plugin Demo](https://github.com/microsoft/TaskWeaver/assets/7489260/7f819524-2c5b-46a8-9c0c-e001a2c7131b)

# How to Use

To enable this role, you need to add `web_explorer` to the `session.roles` list in the project configuration file `project/taskweaver_config.json`.
In addition, you need to configure the GPT4-Vision model's API key and endpoint in the project configuration file `project/taskweaver_config.json`.
The web browser is based on Selenium. You need to install the Chrome browser and download the Chrome driver.
Then, you need to configure the path to the Chrome driver in the project configuration file `project/taskweaver_config.json`.

```json
{
  "session.roles": ["planner","web_explorer"],
  "web_explorer.gpt4v_key": "api_key",
  "web_explorer.gpt4v_endpoint": "endpoint",
  "web_explorer.chrome_driver_path": "path",
  "web_explorer.chrome_executable_path": "path"
}
```

