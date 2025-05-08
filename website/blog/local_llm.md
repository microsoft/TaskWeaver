---
title: Run TaskWeaver with Locally Deployed Not-that-Large Language Models
authors: liqli
date: 2024-07-08
---

:::info
The feature introduced in this blog post can cause incompatibility issue with the previous version of TaskWeaver
if you have customized the examples for the planner and code interpreter. 
The issue is easy to fix by changing the examples to the new schema.
Please refer to the [How we implemented the constrained generation in TaskWeaver](/blog/local_llm#how-we-implemented-the-constrained-generation-in-taskweaver) section for more details.
:::

## Motivation
We've seen many raised issues complaining that it is difficult to run TaskWeaver
with locally deployed non-that-large language models (LLMs), such as 7b or 13b.
When we examine the issues, we find that the main problem is that the models failed 
to generate responses following our formatting instructions in the prompt. For instance,
we see that the planner's response does not contain a `send_to` field, which is required
to determine the recipient of the message.

In the past, we have tried to address this issue by adding more examples in the prompt,
which however did not work well, especially for these relatively small models. Another idea
was to ask the model to re-generate the response if it does not follow the format. 
We include the format error in the prompt to help the model understand the error and
correct it. However, this approach also did not work well. 

<!-- truncate -->

## Constrained Generation

Recently, we discovered a new approach called "Constrained Generation" that can enforce 
the model to generate responses following the format. Popular frameworks include [Outlines](https://github.com/outlines-dev/outlines),
[Guidance](https://github.com/guidance-ai/guidance), [lm-format-enforcer](https://github.com/noamgat/lm-format-enforcer/tree/main), etc.
All these frameworks support generating responses following a specific format, e.g., a JSON schema.
This makes it possible to control the output format by providing it a schema.

In TaskWeaver, a relatively easy way to integrate this feature is to use a local deployment that supports
both constrained generation and OpenAI compatible API, for instance, the [vllm](https://docs.vllm.ai/en/stable/serving/openai_compatible_server.html).
There are other frameworks that support constrained generation, such as llama.cpp. 
But currently, we found that this feature is still not mature enough, so we start with vllm for experimentation.

To run vllm, you can follow the instructions in the [vllm documentation](https://docs.vllm.ai/en/stable/serving/openai_compatible_server.html). 
A simple example is shown below:
```shell
python -m vllm.entrypoints.openai.api_server --model meta-llama/Meta-Llama-3-8B-Instruct --guided-decoding-backend lm-format-enforcer
```
where `--guided-decoding-backend lm-format-enforcer` is used to enable the constrained generation feature and 
specify the backend. Currently, vllm only supports `lm-format-enforcer` and `outlines`.

Here is a sample code to test the vllm server:
```python
from openai import OpenAI

json_schema = {
    "type": "object",
    "properties": {
        "country_name": {
            "type": "string"
        }
    },
    "required": ["country_name"]
}

openai_api_key = "EMPTY"
openai_api_base = "http://localhost:8000/v1"
client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)
completion = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Which country is San Francisco in?"}
    ],
    extra_body={
        "guided_json": json_schema,
        "guided_decoding_backend": "lm-format-enforcer"
    }                           
)
print("Completion result:", completion)
```
If you run the above code, you will get the response following the format specified in the `json_schema`.

After you have successfully deployed vllm, you can set the following configurations in TaskWeaver:
```json
{
    "llm.model": "meta-llama/Meta-Llama-3-8B-Instruct",
    "llm.api_base": "http://localhost:8000/v1",
    "llm.api_key": "null",
    "llm.api_type": "openai",
    "llm.openai.require_alternative_roles": false,
    "llm.openai.support_system_role": true
}
```
The `llm.openai.require_alternative_roles` and `llm.openai.support_system_role` configurations are 
discussed in the [OpenAI Configuration](/docs/configurations/configurations_in_detail) page.
With these configurations, TaskWeaver will send the messages to the vllm server and get the responses.

## How we implemented the constrained generation in TaskWeaver

In order to support the constrained generation in TaskWeaver, we need to provide the schema to the model.
Therefore, we made a few changes in the code to support this feature.

First, we add a `response_json_schema` field to the planner and code interpreter. For planner, you can find
it in `taskweaver/planner/planner_prompt.py`. It looks like this:
```yaml
response_json_schema: |-
  {
    "type": "object",
    "properties": {
        "response": {
            "type": "object",
            "properties": {
                "init_plan": {
                    "type": "string"
                },
                "plan": {
                    "type": "string"
                },
                "current_plan_step": {
                    "type": "string"
                },
                "send_to": {
                    "type": "string"
                },
                "message": {
                    "type": "string"
                }
            },
            "required": [
                "init_plan",
                "plan",
                "current_plan_step",
                "send_to",
                "message"
            ]
        }
    },
    "required": ["response"]
  }
```
If you are familiar with the previous output schema, you may notice that we have changed the `response` field to an object
from an array of elements. This is because that it is much easier to express the schema in JSON format if 
the properties are in an object, not elements in an array.

Correspondingly, we add a `response_json_schema` field to the code interpreter. You can find it in `taskweaver/code_interpreter/code_interpreter/code_generator_prompt.py`,
which looks like this:
```yaml
response_json_schema: |-
    {
        "type": "object",
        "properties": {
            "response": {
                "type": "object",
                "properties": {
                    "thought": {
                        "type": "string"
                    },
                    "reply_type": {
                        "type": "string",
                        "enum": ["python", "text"]
                    },
                    "reply_content": {
                        "type": "string"
                    }   
                },
                "required": ["thought", "reply_type", "reply_content"]
            }
        },
        "required": ["response"]
    } 
```
We also change the `response` field to an object from an array of elements in the code interpreter.
A benefit of this change is that we can now easily restrict the `reply_type` field to only two values: `python` and `text`,
which is not possible before. 

One consequence of this change is that we need to modify the examples for the code interpreter in order
to support the new schema. The old examples contain attachments that have the types of 
`python`, `text`, and `sample`, which are deprecated. We now need to change them to the new schema.
Specifically, we need to change the `type` field to `reply_type` and the `content` field to `reply_content`.
For example, the old example:
```yaml
- type: python
  content: |-
    file_path = "/abc/def.txt"  

    with open(file_path, "r") as file:  
        file_contents = file.read()  
        print(file_contents)
```
should be changed to:
```yaml
- type: reply_type
  content: python # or 'text' if the old type is 'text' or 'sample'
- type: reply_content
  content: |-
    file_path = "/abc/def.txt"  

    with open(file_path, "r") as file:  
        file_contents = file.read()  
        print(file_contents)
```

There could be multiple `thought` attachments in the code interpreter examples.
But in the new schema, there is only one `thought` field. So we have added code to do the conversion and no 
manual work is needed to modify the examples.
If you have examples, after these changes, we can now support the constrained generation in TaskWeaver.

Second, we submit the JSON schema to the model when we need to call the endpoint,
which you can find in `planner.py` and `code_generator.py`, respectively.

## Conclusion

In this blog post, we have introduced a new feature called "Constrained Generation" that can enforce the model to generate responses following the format.
We have also shown how to run TaskWeaver with locally deployed non-that-large language models (LLMs) that support constrained generation.
We have also explained how we implemented the constrained generation in TaskWeaver. We hope this feature can help you run TaskWeaver with LLMs more easily.
If you have any questions or suggestions, please feel free to contact us.





