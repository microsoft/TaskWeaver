---
id: develop_plugin
description: How to develop a new plugin
slug: /plugin/how_to_develop_a_new_plugin
---
# How to develop a new plugin

In this tutorial, we will introduce how to develop a strawman plugin in TaskWeaver. This plugin can render a input text in ascii art. 

## Implement the python code

Create a python file named `ascii_render.py` in the `plugins` folder. The file name should be the same as the plugin name. The plugin name is defined in the plugin schema. In this example, the plugin name is `ascii_render`.
The following code is the template of the plugin implementation.
```python
from taskweaver.plugin import Plugin, register_plugin

@register_plugin
class PluginTemplate(Plugin):
    def __call__(self, *args, **kwargs):
        """Implementation Starts"""
        result, description = YourImplementation()
        """Implementation Ends"""

        # if your want to add artifact from the execution result, uncomment the following code
        # self.ctx.add_artifact(
        #     name="artifact",
        #     file_name="artifact.csv",
        #     type="df",
        #     val=result,
        # )
        return result, description
```

The typical way of implementing the plugin is to change the code between `Implementation Starts` and `Implementation Ends`. Note that the return are two variables _result_ and _description_. The _result_ stores whatever output required for follow-up processing (e.g., a DataFrame). The _description_ is a string to describe the result. 

Let's make some changes to the code and the result is as follows:

```python
from taskweaver.plugin import Plugin, register_plugin

@register_plugin
class AsciiRenderPlugin(Plugin):
    def __call__(self, text: str):
        import pyfiglet
        ascii_art_str = pyfiglet.figlet_format(text, font='isometric1')
        return ascii_art_str
```
Note that this function depends on the package `pyfiglet`, so we need to install it with `pip install pyfiglet`.

## Configure the schema

Next, we need to configure the schema so that the LLM can understand the function 
of the plugin. In the schema, there are several fields that should be filled, 
including `name`, `enabled`, `required`, `description`, `parameters` and `returns`. 
Please check [Plugin Introduction](https://microsoft.github.io/TaskWeaver/docs/plugin/plugin_intro) 
for more details. 
Create a yaml file named `ascii_render.yaml` and copy the following content into it.

```yaml
name: ascii_render
enabled: true
required: true
description: >-
  This plugin renders the input text into ASCII art form. 
  The input should be a string and the output is also a string in ASCII art.
  For example, result = ascii_render(text='Hello World').

parameters:
  - name: text
    type: str
    required: true
    description: >-
      This is the input text to be rendered into ASCII art form.

returns:
  - name: result
    type: str
    description: >-
      The rendered text in ASCII art.
```

## Call the plugin

After the plugin is implemented and configured, we can call the plugin in the conversation.
The full conversation is as follows:
```bash
=========================================================
 _____         _     _       __
|_   _|_ _ ___| | _ | |     / /__  ____ __   _____  _____
  | |/ _` / __| |/ /| | /| / / _ \/ __ `/ | / / _ \/ ___/
  | | (_| \__ \   < | |/ |/ /  __/ /_/ /| |/ /  __/ /
  |_|\__,_|___/_|\_\|__/|__/\___/\__,_/ |___/\___/_/
=========================================================
TaskWeaver: I am TaskWeaver, an AI assistant. To get started, could you please enter your request?
Human: render ABC in ascii art
>>> [INIT_PLAN]
1. Render the text 'ABC' into ASCII art
>>> [PLAN]
1. Instruct CodeInterpreter to render the text 'ABC' into ASCII art
>>> [CURRENT_PLAN_STEP]
1. Instruct CodeInterpreter to render the text 'ABC' into ASCII art
>>> [SEND_TO]
CodeInterpreter
>>> [MESSAGE]
Please render the text 'ABC' into ASCII art
>>> [PLANNER->CODEINTERPRETER]
Please render the text 'ABC' into ASCII art
>>> [PYTHON]
# Call the plugin function to render the text 'ABC' into ASCII art
ascii_art_result = ascii_render("ABC")
ascii_art_result
>>> [VERIFICATION]
NONE
>>> [STATUS]
SUCCESS
>>> [RESULT]
The execution of the generated python code above has succeeded

The result of above Python code after execution is:
      ___           ___           ___     
     /\  \         /\  \         /\  \    
    /::\  \       /::\  \       /::\  \   
   /:/\:\  \     /:/\:\  \     /:/\:\  \  
  /::\~\:\  \   /::\~\:\__\   /:/  \:\  \ 
 /:/\:\ \:\__\ /:/\:\ \:|__| /:/__/ \:\__\
 \/__\:\/:/  / \:\~\:\/:/  / \:\  \  \/__/
      \::/  /   \:\ \::/  /   \:\  \      
      /:/  /     \:\/:/  /     \:\  \     
     /:/  /       \::/__/       \:\__\    
     \/__/         ~~            \/__/    

>>> [CODEINTERPRETER->PLANNER]
The following python code has been executed:

# Call the plugin function to render the text 'ABC' into ASCII art
ascii_art_result = ascii_render("ABC")
ascii_art_result



The execution of the generated python code above has succeeded

The result of above Python code after execution is:
      ___           ___           ___     
     /\  \         /\  \         /\  \    
    /::\  \       /::\  \       /::\  \   
   /:/\:\  \     /:/\:\  \     /:/\:\  \  
  /::\~\:\  \   /::\~\:\__\   /:/  \:\  \ 
 /:/\:\ \:\__\ /:/\:\ \:|__| /:/__/ \:\__\
 \/__\:\/:/  / \:\~\:\/:/  / \:\  \  \/__/
      \::/  /   \:\ \::/  /   \:\  \      
      /:/  /     \:\/:/  /     \:\  \     
     /:/  /       \::/__/       \:\__\    
     \/__/         ~~            \/__/    

>>> [INIT_PLAN]  
1. Render the text 'ABC' into ASCII art
>>> [PLAN]
1. Instruct CodeInterpreter to render the text 'ABC' into ASCII art
>>> [CURRENT_PLAN_STEP]
Report the ASCII art to the user
>>> [SEND_TO]
User
>>> [MESSAGE]
Here is the text 'ABC' rendered in ASCII art:
      ___           ___           ___     
     /\  \         /\  \         /\  \    
    /::\  \       /::\  \       /::\  \   
   /:/\:\  \     /:/\:\  \     /:/\:\  \  
  /::\~\:\  \   /::\~\:\__\   /:/  \:\  \ 
 /:/\:\ \:\__\ /:/\:\ \:|__| /:/__/ \:\__\
 \/__\:\/:/  / \:\~\:\/:/  / \:\  \  \/__/
      \::/  /   \:\ \::/  /   \:\  \      
      /:/  /     \:\/:/  /     \:\  \     
     /:/  /       \::/__/       \:\__\    
     \/__/         ~~            \/__/    
>>> [PLANNER->USER]
Here is the text 'ABC' rendered in ASCII art:
      ___           ___           ___     
     /\  \         /\  \         /\  \    
    /::\  \       /::\  \       /::\  \   
   /:/\:\  \     /:/\:\  \     /:/\:\  \  
  /::\~\:\  \   /::\~\:\__\   /:/  \:\  \ 
 /:/\:\ \:\__\ /:/\:\ \:|__| /:/__/ \:\__\
 \/__\:\/:/  / \:\~\:\/:/  / \:\  \  \/__/
      \::/  /   \:\ \::/  /   \:\  \      
      /:/  /     \:\/:/  /     \:\  \     
     /:/  /       \::/__/       \:\__\    
     \/__/         ~~            \/__/    
TaskWeaver: Here is the text 'ABC' rendered in ASCII art:
      ___           ___           ___     
     /\  \         /\  \         /\  \    
    /::\  \       /::\  \       /::\  \   
   /:/\:\  \     /:/\:\  \     /:/\:\  \  
  /::\~\:\  \   /::\~\:\__\   /:/  \:\  \ 
 /:/\:\ \:\__\ /:/\:\ \:|__| /:/__/ \:\__\
 \/__\:\/:/  / \:\~\:\/:/  / \:\  \  \/__/
      \::/  /   \:\ \::/  /   \:\  \      
      /:/  /     \:\/:/  /     \:\  \     
     /:/  /       \::/__/       \:\__\    
     \/__/         ~~            \/__/        
```

## FAQ
**Q: How do I know if TaskWeaver can see my plugin?**

A: A simple way to check if TaskWeaver can see your plugin is to ask "What can you do?" to TaskWeaver.
The typical response is to list all the available plugins like the following:
```markdown
I can assist you with various tasks, including:

- Detecting anomalies in time series data.
- Rendering text into ASCII art.
- Searching and comparing prices from thousands of online shops (US only).
- Telling a joke.

If you have a specific task in mind, please let me know, and I'll do my best to assist you.
```
If you see your plugin in the list, it means TaskWeaver can see your plugin.
But this is not a reliable way to check if TaskWeaver can see your plugin because the response is generated by the LLM.
A more reliable way is to check the prompt of the Planner. You can find the prompts 
from `project/workspace/sessions/<session_id>/planner_prompt_log_xxxx.yaml`.
Then, search for this section as follows:

```markdown
CodeInterpreter has the following plugin functions and their required parameters need to be provided before the execution:
- anomaly_detection: anomaly_detection function identifies anomalies from an input DataFrame of time series. It will add a new column \"Is_Anomaly\", where each entry will be marked with \"True\" if the value is an anomaly or \"False\" otherwise. Arguments required: df: DataFrame, time_col_name: str, value_col_name: str
- ascii_render: This plugin renders the input text into ASCII art form. Arguments required: text: str
- klarna_search: Search and compare prices from thousands of online shops. Only available in the US. This plugin only takes user requests when searching for merchandise. If not clear, confirm with the user if they want to search for merchandise from Klarna. Arguments required: query: str
- tell_joke: Call this plugin to tell a joke.
```
Check if your plugin is in the list. If it is, it means TaskWeaver can see your plugin.

**Q: Why TaskWeaver cannot see my plugin?**

First, make sure you have read our [Plugin Introduction](https://microsoft.github.io/TaskWeaver/docs/plugin/plugin_intro) and this tutorial carefully.
You should have two files in the `plugins` folder, e.g., `ascii_render.py` and `ascii_render.yaml`.

Now, if TaskWeaver cannot see your plugin, the root cause is typically syntax errors in the yaml file. 
Check the console output if you are using the command line interface, or the console logs if you are using the web interface.
You may see the following error message:
```bash
failed to loading component from <name>.yaml, skipping: Yaml loading failed due to: <reason>
```
The error message will tell you the reason why the yaml file cannot be loaded.
It is typically easy to fix the syntax errors by using a yaml linter (e.g., in Visual Studio Code) or an online yaml linter.

If you have checked the syntax of the yaml file and TaskWeaver still cannot see your plugin, please check
if the yaml file has included all the required fields such as the `parameters` and `returns` fields.


**Q: Why TaskWeaver can see my plugin but cannot call it?**

A: In this case, you may see the generated code has called the plugin function, 
but the execution result is an error message saying that the plugin function is undefined.
If this happens, please check the console output if you are using the command line interface,
or the console logs if you are using the web interface.

You may see the following error message:
```bash
Plugin <name> failed to load: Plugin <name> failed to register: failed to load plugin <name> <reason>
```
This error message will tell you the reason why the plugin function cannot be loaded.
It is typically easy to fix the errors by checking the console output or logs.
The root cause is typically errors in the python file that causes the plugin function cannot be loaded.
Typical errors include syntax errors, missing imports, or missing packages.

Note that this sort of error is not caused by the implementation "inside" the plugin function.
Otherwise, the errors would be caught during the execution of the plugin function, 
not during the loading of the plugin function.

**Q: How to debug my plugin?**

A: We are working on a debugging tool to help you debug your plugin. For now, a simple way to debug your plugin is to 
define a main function in the python file and run it in your local environment.
For example, you can define a main function in `ascii_render.py` as follows:
```python
if __name__ == "__main__":
    from taskweaver.plugin.context import temp_context

    with temp_context() as temp_ctx:
        render = AsciiRenderPlugin(name="ascii_render", ctx=temp_ctx, config={})
        print(render(text="hello world!"))
```
In this main function, we create a temporary context and call the plugin function with some input.
You need not change the plugin implementation. Just add the main function to the end of the python file.
Then, run the python file in your local environment. If there are any errors, you can see them in the console output.

If you have the `configurations` section in the yaml file, you can manually set the configurations in the `config` parameter of the plugin constructor.
We currently do not read the yaml file, so you need to make sure that the configurations are set correctly in the `config` parameter.
For example, if an integer configuration `max_length` is defined in the yaml file, you can set it in the `config` parameter as follows:
```python
config = {
    "max_length": 100
}
```
Then, pass the `config` to the plugin constructor. As yaml is type sensitive, you need to make sure that the type of the configuration is correct.