# Plugins In-Depth

_**Pre-requisites**: Please refer to the [Introduction](/docs/plugin/plugin_intro) and the [Plugin Development](/docs/plugin/how_to_develop_a_new_plugin) 
pages for a better understanding of the plugin concept and its development process._

## Plugin Basics
In TaskWeaver, the plugins are the essential components to extend the functionality of the agent.
Specifically, a plugin is a piece of code wrapped in a class that can be called as a function by the agent in the generated code snippets.
The following is a simple example of a plugin that generates `n` random numbers:

```python
from taskweaver.plugin import Plugin, register_plugin

@register_plugin
class RandomGenerator(Plugin):
    def __call__(self, n: int):
        import random
        return [random.randint(1, 100) for _ in range(n)]
```

In this example, the `RandomGenerator` class inherits the `Plugin` class and implements the `__call__` method, which means
it can be called as a function. What would be the function signature of the plugin? 
It is defined in the associated YAML file. For example, the YAML file for the `RandomGenerator` plugin is as follows:

```yaml
name: random_generator
enabled: true
required: true
description: >-
  This plugin generates n random numbers between 1 and 100.
examples: |-
  result = random_generator(n=5)
parameters:
  - name: n
    type: int
    required: true
    description: >-
      The number of random numbers to generate.

returns:
  - name: result
    type: list
    description: >-
      The list of random numbers.
```

The YAML file specifies the name, description, parameters, and return values of the plugin. 
When the LLM generates the code snippets, it will use the information in the YAML file to generate the function signature.
We did not check the discrepancy between the function signature in the Python implementation and the YAML file. 
So, it is important to keep them consistent.
The `examples` field is used to provide examples of how to use the plugin for the LLM.

## Configurations and States

Although the plugin is used as a function in the code snippets, it is more than a normal Python function.
The plugin can have its own configurations and states.
For example, the `RandomGenerator` plugin can have a configuration to specify the range of the random numbers.
The configurations can be set in the YAML file as follows:

```yaml
# the previous part of the YAML file
configurations:
  - name: range
    type: list
    required: false
    description: >-
      The range of the random numbers.
    default: [1, 100]
```
We did not show how to use the configurations in the plugin implementation, 
which could be found in one of our sample plugins, namely [sql_pull_data](https://github.com/microsoft/TaskWeaver/blob/main/project/plugins/sql_pull_data.yaml).
Supporting configurations in the plugin is a powerful feature to make the plugin more flexible and reusable.
For example, we can have multiple YAML files pointing to the same Python implementation but with different configurations.
Read this [page](/docs/plugin/multi_yaml_single_impl) for more details. When TaskWeaver loads the plugins, 
it will elaborate the YAML files and create the plugin objects with the configurations. Therefore, two plugins with the same Python implementation 
but different configurations are actually different objects in memory. 
That is why different plugins can have different states, and this is especially helpful when the plugin needs 
to maintain some states across different calls. Consider the example of the `sql_pull_data` sample plugin, which has the following
code snippet:

```python
@register_plugin
class SqlPullData(Plugin):
    db = None

    def __call__(self, query: str):
        ...

        if self.db is None:
            self.db = SQLDatabase.from_uri(self.config.get("sqlite_db_path"))
```
In the example above, the `SqlPullData` plugin maintains a database connection across different calls. 
If we design the plugin to be a stateless normal Python function, we would need to establish a new connection for each call,
which is inefficient and not necessary. 

## The Plugin Lifecycle

The plugin lifecycle is the process of how the plugin is loaded, initialized, and called by the agent.
When TaskWeaver starts, it goes through all the plugin configuration files in the `plugins` directory 
and creates the plugin entries in the memory. The Python implementation of the plugin is not loaded at this stage.
When the agent generates the code snippets, it will call the plugin by the name specified in the YAML file,
and fill in the function signature based on the information in the YAML file.

The plugin is loaded and initialized when the code executor executes the code snippets for the first time
in a session.
The plugin is initialized with the configurations specified in the YAML file.
Although we have the [feature](/docs/advanced/plugin_selection) to dynamically select the plugins in the LLM, all the plugins are loaded 
no matter whether they are used in the current conversation round. The only way of controlling the plugin loading is to 
enable or disable the plugin in the YAML file. 
In theory, the plugins can be configured separately for different sessions. 
For example, when a user starts a new session, we can load a different set of plugins based on the user's profile.
But this feature is **not** supported in TaskWeaver yet.

The plugin is called when the agent executes the code snippets. The plugin can maintain states across different calls,
which has been discussed in the previous section. As each session is associated with a Jupyter kernel,
the plugin objects are created in the kernel memory and can be accessed across different code snippets, from different code cells, 
in the same session.
When the session is closed, the plugin objects are also destroyed with the kernel.

## Conclusion
In this page, we discussed the basics of the plugin in TaskWeaver, including the plugin implementation, the YAML file,
the configurations, and the states. We also introduced the plugin lifecycle, which is the process of how the plugin is loaded, initialized, and called by the agent.
The plugin is a powerful component in TaskWeaver to extend the functionality of the agent.
