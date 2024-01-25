---
id: multi_yaml_single_impl
description: Multiple YAML files to one Python implementation
slug: /plugin/multi_yaml_single_impl
---

# Multiple YAML files to one Python implementation

In practice, you may want to have multiple plugins that share the same implementation.
For example, you may want to have two plugins that both pull data from a database, but one pulls data from database A and the other pulls data from database B.
In this case, the plugin implementation code is the same, but the plugin configuration is different.
It would be cumbersome to copy and paste the same implementation code to two different files.

To solve this problem, TaskWeaver allows you to have multiple plugin configurations that share the same implementation.
Here is an example of the plugin configuration for the two plugins that pull data from database A and B respectively:

The configuration for the plugin that pulls data from database A:
```yaml
name: sql_pull_data_from_A
code: sql_pull_data
...
description: >-
  Pull data from a SQL database A. The database A contains information about merchandise sales.
examples: |-
  df, description = sql_pull_data_from_A("pull data from time_series table")
parameters:
  ...
returns:
  ...
configurations:
  ...
  sqlite_db_path: /path/to/sqlite_A.db
```

The configuration for the plugin that pulls data from database B:
```yaml
name: sql_pull_data_from_B
code: sql_pull_data
...
description: >-
  Pull data from a SQL database B. The database B contains information about customer information.
examples: |-
  df, description = sql_pull_data_from_B("pull data from time_series table")
parameters:
  ...
returns:
  ...
configurations:
  ...
  sqlite_db_path: /path/to/sqlite_B.db
```

Let's discuss the differences between the two configurations. 

First, you can see that the `name` field is different, and the names are different from the python file name (without extension) which is `sql_pull_data.py`.
This name is used in CodeInterpreter for code generation. So, you can see that in the `examples` field, 
the function name is `sql_pull_data_from_A` and `sql_pull_data_from_B`, respectively.

Second, you can see that the `code` field is the same, and the code file name is `sql_pull_data.py`.
This means that the two plugins share the same implementation code. 
The `code` field is optional, and if you don't specify it, the plugin name will be used as the code file name without the extension.

Third, you can see that the `configurations` field is different, and the `sqlite_db_path` is different.
This means that the two plugins have different configurations.
This is typically the key reason why you want to have multiple plugin configurations that share the same implementation.

Finally, you can see that the `description` field is different, and the descriptions are different.
This is important because the Planner and the CodeInterpreter will use the description to make decisions and generate code.
The two descriptions should be explicit enough to distinguish the two plugins. 
Otherwise, the Planner and the CodeInterpreter may not be able to make the right decisions.

## Conclusion
When you meet the situation where you want to have multiple plugin configurations that share the same implementation,
you can use the `code` field to specify the code file name, and use the `configurations` field to specify the configurations.
The `name` field is used to distinguish the plugins, and the `description` field is used to 
help the Planner and the CodeInterpreter make right decisions.



