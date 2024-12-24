---
id: observability
description: Observability
slug: /observability
---

# Observability

[AgentOps](https://www.agentops.ai/) is a platform that helps you to monitor and analyze the behavior and performance of your agents. 
TaskWeaver is integrated with AgentOps, so you can use TaskWeaver to generate code and use AgentOps to observe all the events from the planning to the code execution.

## Get Started

TaskWeaver integration with AgentOps is documented [here](https://docs.agentops.ai/v1/integrations/taskweaver).

To get started, you need an API key from AgentOps by [signing up](https://app.agentops.ai/signup) for a free account. Then you need to create a new project and generate the API key from the project settings.

Once you have the API keys, the following steps will help you to get started.

1. Install the `agentops`` package in your project.
   ```bash
   pip install agentops
   ```
2. Import the `agentops` package in your project.
   ```python
   import agentops
   ```
3. Initialize the `agentops` client with your API key.
   ```python
   agentops.init(api_key="your_api_key")
   ```

   :::note
   You can also set the tags here to track your sessions in the AgentOps dashboard. By default, the "taskweaver" tag will be added to all the AgentOps sessions for TaskWeaver.
   :::

4. Import the TaskWeaver handler `TaskWeaverEventHandler` and set it as the event handler for your TaskWeaver project.
   ```python
   from agentops.providers.taskweaver import TaskWeaverEventHandler
   handler = TaskWeaverEventHandler()
   ```

   :::note
   There are two ways to set the handler:
   - Set the handler using the `session.event_handler.register()` method.
   - Set the handler in every `session.send_message` function call in the `event_handler` parameter.
   :::

   :::warning
   If you encounter "stuttering" in the recorded messages from the events, it is because the handler has been set with more than one instance.
   :::

5. Now you can run your TaskWeaver project and observe the events in the AgentOps dashboard. When the client is initialized, it will automatically start to track the events and provide a link to the session in the AgentOps dashboard.

:::info
It is important to note that the LLM calls and the other events are tracked together in different modules of AgentOps. By default, all the LLM calls are tracked when the AgentOps client is initialized. However, the other events are only tracked when the `TaskWeaverEventHandler` handler is used in conjunction within the code.

Therefore, event observability is limited to LLM calls when TaskWeaver is used in [Terminal mode](../usage/cmd.md).
:::
