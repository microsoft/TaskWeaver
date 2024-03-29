---
id: plugin_intro
description: Plugin introduction
slug: /plugin/plugin_intro
---

# Plugin Introduction

Plugins are the units that could be orchestrated by TaskWeaver. One could view the plugins as tools that the LLM can
utilize to accomplish certain tasks.

In TaskWeaver, each plugin is represented as a Python function that can be called within the generated code snippet. 
One concrete example would be pulling data from database and apply anomaly detection. The generated code (simplified) looks like
follows:

```python
df, data_description = sql_pull_data(query="pull data from time_series table")  
anomaly_df, anomaly_description = anomaly_detection(df, time_col_name="ts", value_col_name="val") 
```
The generated code snippet above calls two plugins: `sql_pull_data` and `anomaly_detection`. The `sql_pull_data` plugin
pulls data from a database, and the `anomaly_detection` plugin detects anomalies in the data.

## Plugin Structure

A plugin involves two files:

* **Plugin Implementation**: a Python file that defines the plugin
* **Plugin Schema**: a file in yaml that defines the schema of the plugin

## Plugin Implementation

The plugin function needs to be implemented in Python.
To be coordinated with the orchestration by TaskWeaver, a plugin python file consists of two parts:

- Plugin function implementation code
- TaskWeaver plugin decorator

Here we exhibit an example of the anomaly detection plugin as the following code:

```python
import pandas as pd
from pandas.api.types import is_numeric_dtype

from taskweaver.plugin import Plugin, register_plugin


@register_plugin
class AnomalyDetectionPlugin(Plugin):
    def __call__(self, df: pd.DataFrame, time_col_name: str, value_col_name: str):

        """
        anomaly_detection function identifies anomalies from an input dataframe of time series.
        It will add a new column "Is_Anomaly", where each entry will be marked with "True" if the value is an anomaly
        or "False" otherwise.

        :param df: the input data, must be a dataframe
        :param time_col_name: name of the column that contains the datetime
        :param value_col_name: name of the column that contains the numeric values.
        :return df: a new df that adds an additional "Is_Anomaly" column based on the input df.
        :return description: the description about the anomaly detection results.
        """
        try:
            df[time_col_name] = pd.to_datetime(df[time_col_name])
        except Exception:
            print("Time column is not datetime")
            return

        if not is_numeric_dtype(df[value_col_name]):
            try:
                df[value_col_name] = df[value_col_name].astype(float)
            except ValueError:
                print("Value column is not numeric")
                return

        mean, std = df[value_col_name].mean(), df[value_col_name].std()
        cutoff = std * 3
        lower, upper = mean - cutoff, mean + cutoff
        df["Is_Anomaly"] = df[value_col_name].apply(lambda x: x < lower or x > upper)
        anomaly_count = df["Is_Anomaly"].sum()
        description = "There are {} anomalies in the time series data".format(anomaly_count)
        
        self.ctx.add_artifact(
             name="anomaly_detection_results",  # a brief description of the artifact
             file_name="anomaly_detection_results.csv",  # artifact file name
             type="df",  # artifact data type, support chart/df/file/txt/svg
             val=df,  # variable to be dumped
        )
        
        return df, description

```

You need to go through the following steps to register a plugin:

1. import the TaskWeaver plugin decorator `from taskWeaver.plugin import Plugin, register_plugin`
2. create your plugin class inherited from `Plugin` parent class (e.g., `AnomalyDetectionPlugin(Plugin)`), which is
   decorated by `@register_plugin`
3. implement your plugin function in `__call__` method of the plugin class.  

We provide an example process of developing a new plugin in [this tutorial](./how_to_develop_a_new_plugin.md).

:::tip
A good practice in a plugin implementation is to return a description of
the result in natural language. As LLMs only understand natural language, it is important to let the model understand
what the execution result is. In the example implementation above, the description says how many anomalies are detected.
In other cases such as loading a csv file, a good description could be showing the schema of the loaded data.
This description can be used by the LLM to plan the next steps.
:::

### Important Notes

1. If the functionality of your plugin depends on additional libraries or packages, it is essential to ensure that they
   are installed before proceeding.

2. If you wish to persist intermediate results, such as data, figures, or prompts, in your plugin implementation,
   TaskWeaver provides an `add_artifact` API that allows you to store these results in the workspace. In the example we
   provide, if you have performed anomaly detection and obtained results in the form of a CSV file, you can utilize
   the `add_artifact` API to save this file as an artifact. The artifacts are stored in the `project/workspace/session_id/cwd` folder in the project directory.

   ```python
   self.ctx.add_artifact(
       name="anomaly_detection_results",  # a brief description of the artifact
       file_name="anomaly_detection_results.csv",  # artifact file name
       type="df",  # artifact data type, support chart/df/file/txt/svg
       val=df,  # variable to be dumped
   )
   ```

## Plugin Schema

The plugin schema is composed of several parts:

- ***name**: The main function name of the Python code.
- **enabled**: determine whether the plugin is enabled for selection during conversations. The default value is true.
- **plugin_only**: determine if this plugin is enabled under the plugin-only mode. The default value is false.
- **code**: the code file name of the plugin. The default value is the same as the plugin name.
- ***descriptions**: A brief description that introduces the plugin function.
- ***parameters**: This section lists all the input parameter information. It includes the parameter's name, type,
whether it is required or optional, and a description providing more details about the parameter.
- ***returns**: This section lists all the return value information. It includes the return value's name, type, and
description that provides information about the value that is returned by the function.
- **configurations**: the configuration parameters for the plugin. The default value is an empty dictionary.

:::tip
The addition of any extra fields or missing of mandatory fields (marked by * above) would result in a validation failure within the plugin schema.
:::

The plugin schema is required to be written in YAML format. Here is the plugin schema example of the above anomaly
detection plugin:

```yaml
name: anomaly_detection
enabled: true
plugin_only: false
required: false
description: >-
  anomaly_detection function identifies anomalies from an input DataFrame of
  time series. It will add a new column "Is_Anomaly", where each entry will be marked with "True" if the value is an anomaly or "False" otherwise.

parameters:
  - name: df
    type: DataFrame
    required: true
    description: >-
      the input data from which we can identify the anomalies with the 3-sigma
      algorithm.
  - name: time_col_name
    type: str
    required: true
    description: name of the column that contains the datetime
  - name: value_col_name
    type: str
    required: true
    description: name of the column that contains the numeric values.

returns:
  - name: df
    type: DataFrame
    description: >-
      This DataFrame extends the input DataFrame with a newly-added column
      "Is_Anomaly" containing the anomaly detection result.
  - name: description
    type: str
    description: This is a string describing the anomaly detection results.

```

:::info
Without specifying the `code` field, the plugin schema will use the plugin name as the code file name.
For example, the plugin name is `anomaly_detection` and the code file name is `anomaly_detection.py`.
In cases where the plugin name is not the same as the code file name, you can specify the code name (code file) in
the plugin schema to ensure clarity and accuracy. For example, the plugin name is `anomaly_detection` and the code
file name is `anomaly_detection_code.py`. Then, you can specify the code name in the plugin schema as follows:
```yaml
code: anomaly_detection_code
```
Note that the code file name should be the same as the code name without the `.py` extension.
Refer to [Multiple YAML files to one Python implementation](./multi_yaml_single_impl.md) for more information on how to 
use this feature.
:::

:::info
When using common code that requires some configuration parameter modifications for different
plugins, it is important to specify these configuration parameters in the plugin schema.
The configuration parameters are specified in the plugin schema as follows:
```yaml
 configurations:
   key1: value1
   key2: value2
 ```
These configuration parameters can be accessed in the plugin implementation as follows:
```python
self.config.get("key1")
self.config.get("key2")
```
:::

:::info
When this plugin is enabled for the [plugin-only mode](../../advanced/plugin_only.md), set the `plugin_only` field to `true`.
The default value is `false`. Note that all plugins will be loaded in the non-plugin-only mode which is the default mode. 
But in the plugin-only mode, only the plugins with `plugin_only: true` will be loaded. 
:::
      
   

