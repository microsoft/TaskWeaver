## Plugin Introduction

Plugins are the units that could be orchestrated by TaskWeaver. One could view the plugins as tools that the LLM can
utilize to accomplish certain tasks.

In TaskWeaver, each plugin is represented as a Python function that can be called within a code snippet. The
orchestration is essentially the process of generating Python code snippets consisting of a certain number of plugins.
One concrete example would be pulling data from database and apply anomaly detection. The generated code (simplified) looks like
follows:

```python
df, data_description = sql_pull_data(query="pull data from time_series table")  
anomaly_df, anomaly_description = anomaly_detection(df, time_col_name="ts", value_col_name="val") 
```

## What a plugin have?

A plugin has two files:

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

from taskWeaver.plugin import Plugin, register_plugin


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

You need to go through the following steps to implement your own plugin.

1. import the TaskWeaver plugin decorator `from taskWeaver.plugin import Plugin, register_plugin`
2. create your plugin class inherited from `Plugin` parent class (e.g., `AnomalyDetectionPlugin(Plugin)`), which is
   decorated by `@register_plugin`
3. implement your plugin function in `__call__` method of the plugin class.  **Most importantly, it is mandatory to
   include `descriptions` of your execution results in the return values of your plugin function**. These descriptions
   can be utilized by the LLM to effectively summarize your execution results.

> 💡A key difference in a plugin implementation and a normal python function is that it always return a description of
> the result in natural language. As LLMs only understand natural language, it is important to let the model understand
> what the execution result is. In the example implementation above, the description says how many anomalies are detected.
> Behind the scene, only the description will be passed to the LLM model. In contrast, the execution result (e.g., df in
> the above example) is not handled by the LLM.

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

1. **name**: The main function name of the Python code.
2. **enabled**: determine whether the plugin is enabled for selection during conversations. The default value is true.
3. **descriptions**: A brief description that introduces the plugin function.
4. **parameters**: This section lists all the input parameter information. It includes the parameter's name, type,
   whether it is required or optional, and a description providing more details about the parameter.
5. **returns**: This section lists all the return value information. It includes the return value's name, type, and
   description that provides information about the value that is returned by the function.

**Note:** The addition of any extra fields would result in a validation failure within the plugin schema.

The plugin schema is required to be written in YAML format. Here is the plugin schema example of the above anomaly
detection plugin:

```yaml
name: anomaly_detection
enabled: true
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

Besides, we also set two optional fields as below:

1. **code**: In cases where multiple plugins map to the same Python code (i.e., the plugin name is different from the
   code name), it is essential to specify the code name (code file) in the plugin schema to ensure clarity and accuracy.
2. **configurations**: When using common code that requires some configuration parameter modifications for different
   plugins, it is important to specify these configuration parameters in the plugin schema.
