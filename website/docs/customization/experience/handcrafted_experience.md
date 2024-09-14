# Handcrafted Experience

We have introduced the motivation of the `experience` module in [Experience](./experience.md).
In the quick start guide, we have shown how to extract experiences and lessons from the current conversation.
However, a more common scenario is that you have a handcrafted experience that you want to use to guide the agent.

## Create a handcrafted experience

To create a handcrafted experience, you need to create a YAML file that contains the experience.
The YAML file should have the following structure:

```yaml
exp_id: the-id-of-the-experience
experience_text: the content of the experience
```
The file should be saved in the `experience` folder in the project directory.
The file name should be prefixed with `handcrafted_exp_{exp_id}`.
For example, if the `exp_id` is `1`, the file name should be `handcrafted_exp_1.yaml`.

:::tip
Do not use underscores in the `exp_id` field in order to avoid conflicts with the file name.
:::

In the `experience_text` field, you can write the content of the experience in Markdown format.
For example:

```yaml
exp_id: 1
experience_text: |-
  - Say "world" if you hear "hello".
  - Say "peace" if you hear "love".
```

## Load the handcrafted experience

Loading the handcrafted experience is the same with loading the extracted experience.
If either `planner.use_experience` or `code_generator.use_experience` is set to `True` in the project configuration file `taskweaver_config.json`, 
the handcrafted experience will be loaded at the time of starting the agent.
If your agent is running, you need to restart the agent to load the handcrafted experience.
