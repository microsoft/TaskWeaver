---
id: develop_plugin
description: How to develop a new plugin
slug: /plugin/how_to_develop_a_new_plugin
---
# An Example of Developing a New Plugin

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

:::info
Check the [FAQs](../../FAQ.md) if you have any issues in developing a plugin before submitting an issue on GitHub.
:::