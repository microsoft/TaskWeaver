# Customizing Examples

There are two types of examples: (1) planning examples and (2) code interpreter examples. 
Planning examples are used to demonstrate how to use TaskWeaver to plan for a specific task. 
Code generation examples are used to demonstrate how to generate code or orchestrate plugins to perform a specific task.

## Planning Examples

A planning example tells LLMs how to plan for a specific query from the user; talk to the code interpreter; 
receive the execution result from the code interpreter; and summarize the execution result.
Before constructing the planning example, we strongly encourage you to go through the
[planner prompt](https://github.com/microsoft/TaskWeaver/blob/main/taskweaver/planner/planner_prompt.yaml).

The following is an example of a planning example which contains 4 posts. 
Each post contains a message, a sender, a receiver, and a list of attachments.
1. The first post is sent from the user to the planner.
   The message is "count the rows of /home/data.csv", which is the same as the user query.
2. The second post is sent from the planner to the code interpreter.
   The message is "Please load the data file /home/data.csv and count the rows of the loaded data".
   The attachment list contains 3 attachments:
   1. The first attachment is the initial plan, which is a markdown string.
   2. The second attachment is the plan, which is a markdown string.
   3. The third attachment is the current plan step, which is a markdown string.
3. The third post is sent from the code interpreter to the planner.
   The message is "Load the data file /home/data.csv successfully and there are 100 rows in the data file".
4. The fourth post is sent from the planner to the user.
   The message is "The data file /home/data.csv is loaded and there are 100 rows in the data file".
   The attachment list contains 3 attachments:
   1. The first attachment is the initial plan, which is the same as the second attachment of the second post.
   2. The second attachment is the plan, which is the same as the third attachment of the second post.
   3. The third attachment is the current plan step, which is a markdown string.

```yaml
enabled: True
rounds:
  - user_query: count the rows of /home/data.csv
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
            3. report the result to the user <interactively depends on 2>
        - type: plan
          content: |-
            1. instruct CodeInterpreter to load the data file and count the rows of the loaded data
            2. report the result to the user
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
              3. report the result to the user <interactively depends on 2>
          - type: plan
            content: |-
              1. instruct CodeInterpreter to load the data file and count the rows of the loaded data
              2. report the result to the user
          - type: current_plan_step
            content: 2. report the result to the user
```

## Code Interpreter Examples

A code interpreter example tells LLMs how to generate code or orchestrate plugins to perform a specific task.
The task is from the planner. Before constructing the code interpreter example, we strongly encourage you to
read the [code generator prompt](https://github.com/microsoft/TaskWeaver/blob/main/taskweaver/code_interpreter/code_generator/code_generator_prompt.yaml). 

The following is an example of a code interpreter example which contains 2 posts.
Each post contains a message, a sender, a receiver, and a list of attachments.

1. The first post is sent from the planner to the code interpreter.
   The message is "Please read file /abc/def.txt".
2. The second post is sent from the code interpreter to the planner.
   The message is "read file /abc/def.txt".
   The attachment list contains 6 attachments:
   1. The first attachment is the thought of the code interpreter, which is a markdown string.
   2. The second attachment is the generated code, which is in python.
   3. The third attachment is the verification status, which is CORRECT, INCORRECT, or NONE.
   4. The fourth attachment is the verification error message, which is a markdown string.
   5. The fifth attachment is the execution status, which is SUCCESS, FAILURE, or NONE.
   6. The sixth attachment is the execution result, which is a markdown string.

```yaml
enabled: True
rounds:
  - user_query: read file /abc/def.txt
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
            content: "{ROLE_NAME} will generate a code snippet to read the file /abc/def.txt and present the content to the user."
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

In this example, `verification` is about whether the generated code is correct or not. 
We implemented a module to verify the generated code. If the code is syntactically incorrect, 
or the code violates the constraints, the verification status will be `INCORRECT` 
and some error messages will be returned.
A verification of NONE means that the code has not been verified, which means verification has been turned off.

In this example, `execution_status` is about whether the generated code can be executed successfully or not.
If the execution is successful, the execution status will be `SUCCESS` and the execution result will be returned.
Otherwise, the execution status will be `FAILURE` and some error messages will be returned.
A execution_status of `NONE` means that the code has not been executed.