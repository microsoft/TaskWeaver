# Customizing Examples

There are currently two types of examples: (1) Planner examples and (2) CodeInterpreter examples. 
Planning examples are used to demonstrate how the Planner should plan for a specific query from the User.
Code generation examples are used to help the CodeInterpreter generate code or orchestrate plugins to perform a specific task.

Both types of examples are actually the conversation between a collection of roles, such as the User, the Planner, and the CodeInterpreter.
Each conversation consists of one or more rounds, and each round has a User query and contains one or more posts.
A post is a message sent from one role to another role, and it may contain some attachments.

One example looks like this:
```yaml
enabled: True
rounds:
   - User_query: ping
     state: created
     post_list:
     - message: ping
       send_from: User
       send_to: Planner
       attachment_list: []
     - message: pong
       send_from: Planner
       send_to: User
       attachment_list: []
```
We explicitly break all examples into the two types only to make it easier to understand and maintain.
When the roles are initialized, each role will only read the examples of its type.

:::tip
All the text field in the examples such as the messages are in Markdown format.
:::

## Planner Examples

A planning example tells LLMs how to plan for a specific query from the User, talk to the CodeInterpreter,
receive the execution result from the CodeInterpreter, and summarize the execution result.

The following is an example of a conversation between the User, the Planner, and the CodeInterpreter.
One of the purposes of this example is to teach the Planner on the annotation of the dependencies between the steps in the plan.
Another purpose is to teach the Planner to follow the right output format.

```yaml
enabled: True
rounds:
  - User_query: count the rows of /home/data.csv
    state: created
    post_list:
      - message: count the rows of /home/data.csv
        send_from: User
        send_to: Planner
        attachment_list:
      - message: Please load the data file /home/data.csv and count the rows of the loaded data
        send_from: Planner
        send_to: CodeInterpreter
        attachment_list:
        - type: init_plan
          content: |-
            1. load the data file
            2. count the rows of the loaded data <sequentially depends on 1>
            3. report the result to the User <interactively depends on 2>
        - type: plan
          content: |-
            1. instruct CodeInterpreter to load the data file and count the rows of the loaded data
            2. report the result to the User
        - type: current_plan_step
          content: 1. instruct CodeInterpreter to load the data file and count the rows of the loaded data
      - message: Load the data file /home/data.csv successfully and there are 100 rows in the data file
        send_from: CodeInterpreter
        send_to: Planner
        attachment_list:
      - message: The data file /home/data.csv is loaded and there are 100 rows in the data file
        send_from: Planner
        send_to: User
        attachment_list:
          - type: init_plan
            content: |-
              1. load the data file
              2. count the rows of the loaded data <sequentially depends on 1>
              3. report the result to the User <interactively depends on 2>
          - type: plan
            content: |-
              1. instruct CodeInterpreter to load the data file and count the rows of the loaded data
              2. report the result to the User
          - type: current_plan_step
            content: 2. report the result to the User
```
:::tip
To better understand the attachments including `init_plan`, `plan`, and `current_plan_step`,  
please refer to the [Planner's prompt](https://github.com/microsoft/TaskWeaver/blob/main/taskweaver/planner/planner_prompt.yaml).
:::

In this example, there are 4 posts:
1. The first post is sent from the User to the Planner.
   The message is "count the rows of /home/data.csv", which must be the same with the User query.
2. The second post is sent from the Planner to the CodeInterpreter.
   The message is "Please load the data file /home/data.csv and count the rows of the loaded data".
   The attachment list contains 3 attachments:
   1. The first attachment is the initial plan.
   2. The second attachment is the final plan.
   3. The third attachment is the current plan step.
3. The third post is sent from the CodeInterpreter to the Planner.
   The message is "Load the data file /home/data.csv successfully and there are 100 rows in the data file".
4. The fourth post is sent from the Planner to the User.
   The message is "The data file /home/data.csv is loaded and there are 100 rows in the data file".
   The attachment list contains 3 attachments, which are the same as the second post.

## CodeInterpreter Examples

A CodeInterpreter example tells CodeInterpreter how to generate code or orchestrate plugins to perform a specific task.
The task is always from the Planner. 

The purpose of this example is to teach CodeInterpreter how to handle errors in execution.

```yaml
enabled: True
rounds:
  - User_query: read file /abc/def.txt
    state: finished
    post_list:
      - message: read file /abc/def.txt
        send_from: Planner
        send_to: CodeInterpreter
        attachment_list: []
      - message: I'm sorry, I cannot find the file /abc/def.txt. An FileNotFoundException has been raised.
        send_from: CodeInterpreter
        send_to: Planner
        attachment_list:
        - type: thought
          content: "{ROLE_NAME} will generate a code snippet to read the file /abc/def.txt and present the content to the User."
        - type: python
          content: |-
            file_path = "/abc/def.txt"  

            with open(file_path, "r") as file:  
                file_contents = file.read()  
                print(file_contents)
        - type: verification
          content: CORRECT
        - type: code_error
          content: No code error.
        - type: execution_status
          content: FAILURE
        - type: execution_result
          content: FileNotFoundException, the file /abc/def.txt does not exist.
```
:::tip
Read the prompt of the code generation to better understand the attachments in the example
[code generator prompt](https://github.com/microsoft/TaskWeaver/blob/main/taskweaver/code_interpreter/code_generator/code_generator_prompt.yaml). 
:::

This conversation has two posts:
1. The first post is sent from the Planner to the CodeInterpreter.
   The message is "Please read file /abc/def.txt".
2. The second post is sent from the CodeInterpreter to the Planner.
   The message is "read file /abc/def.txt".
   The attachment list contains 6 attachments:
   1. The first attachment is the thought of the CodeInterpreter.
   2. The second attachment is the generated code, which is in python.
   3. The third attachment is the verification status, which is CORRECT, INCORRECT, or NONE.
   4. The fourth attachment is the verification error message.
   5. The fifth attachment is the execution status, which is SUCCESS, FAILURE, or NONE.
   6. The sixth attachment is the execution result, which is a markdown string.


In this example, `verification` is about whether the generated code is correct or not. 
We implemented a module to verify the generated code. If the code is syntactically incorrect, 
or the code violates the constraints, the verification status will be `INCORRECT` 
and some error messages will be returned.
A verification of NONE means that the code has not been verified, which means verification has been turned off.

In this example, `execution_status` is about whether the generated code can be executed successfully or not.
If the execution is successful, the execution status will be `SUCCESS` and the execution result will be returned.
Otherwise, the execution status will be `FAILURE` and some error messages will be returned.
A execution_status of `NONE` means that the code has not been executed.