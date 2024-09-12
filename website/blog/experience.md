# Experience selection

We have introduced the motivation of the `experience` module in [Experience](/docs/customization/experience/experience) 
and how to create a handcrafted experience in [Handcrafted Experience](/docs/customization/experience/handcrafted_experience).
In this blog post, we discuss more advanced topics about the experience module on experience selection.



## Static experience selection

Every role in TaskWeaver can configure its own experience directory, which can be configured 
by setting the `role_name.experience_dir` field in the project configuration file.
For the `Planner` and `CodeInterpreter` roles, you can configure the experience directory
by setting the `planner.experience_dir` and `code_interpreter.experience_dir` fields respectively.
The default experience directory is `experience` in the project directory.



:::info
The role name is by default the name of the implementation file of the role unless
you have specified the role name by calling `_set_name` in the implementation file.
:::

By configuring different experience directories for different roles, 
you can have different experiences for different roles in a static way.
Use the `Planner` role as an example, you can have the following project configuration file 
to enable the experience selection for the `Planner` role.

```json
{
  "planner.use_experience": true,
  "planner.experience_dir": "planner_exp_dir"
}
```

<!-- truncate -->

## Dynamic experience selection

In some cases, you may want to select the experience dynamically based on the input task.
In TaskWeaver, although we retrieve the experience based on the query content,
it is sometimes difficult to obtain the right experience based solely on the similarity 
between the query content and the experience content. 

One real example we encountered is that we need to retrieve the experience based on the
task type. We have many task types in the project, let's say `task_type_1`, `task_type_2`, and `task_type_3`.
Every task type is about following a set of instructions to complete a task.
Although different task types have different instructions, the instructions are similar in structure.
For example, they all have similar steps like `step_1`, `step_2`, and `step_3`, only 
the content of the steps is slightly different for different task types. 
Actually, even most of the step titles are the same for different task types.

Each task type has its own experience, and we want to select the experience based on the task type.
Even though we can mix all the experiences into one experience directory, it is very hard 
to differentiate the experiences based on the user input or the step content. 
In this project, the user input is simply a task ID, and we need to first figure out the task type based on the task ID,
and then select the experience based on the task type.

To achieve this, we add a layer in the experience selection process. Specifically, we allow
having subdirectories in the experience directory.
For example, we can have the following experience directory structure:

```
planner_experience
├── task_type_1
│   ├── exp_1.yaml
│   ├── exp_2.yaml
│   └── ...
```

When we can identify the task type based on the task ID, we can set the experience subdirectory.
This looks straightforward, but how can we set the experience subdirectory in TaskWeaver?
As we need to do this in a dynamic way, the only way is to set the experience subdirectory in a [role](/docs/concepts/role).
We can add a new role called `TaskTypeIdentifier` to identify the task type based on the task ID.
The key part of the `reply` function in `TaskTypeIdentifier` is shown below:

```python
def reply(self, memory: Memory, **kwargs: ...) -> Post:
    # ...
    # get the task type from the last post message
    task_type = get_task_type(last_post.message)
    # issue a signal to set the experience subdirectory
    post_proxy.update_attachment(
        type=AttachmentType.signal,
        message=f"_signal_exp_sub_path:{task_type}",
    )

    return post_proxy.end()
```

In the `reply` method, we first obtain the query from the last round.
Then we identify the task type based on the query content.
The interesting part is that we set the experience subdirectory in the attachment of the response.
We set the attachment type to `signal` and the message to `_signal_exp_sub_path:{task_type}`.

The `signal` attachment type is a special type in TaskWeaver, which is used to send signals to other roles.
Its content is a string with format `key:value`, where `key` is an attachment type and `value` is the content of the attachment.
In this case, we send a signal to all roles to set the experience subdirectory to the value of `task_type`.
This is done by broadcasting an attachment with type `_signal_exp_sub_path` and its value, which is the task type, 
to all the roles in TaskWeaver. Every role can decide whether to use the signal or not.

A role responds to the signal by setting the experience subdirectory to the value in the signal.
The key part of the `Planner` role implementation is shown below:

```python
# obtain the experience subdirectory from the attachment of the last post
exp_sub_path = last_post.get_attachment(AttachmentType._signal_exp_sub_path)
if exp_sub_path:
    self.tracing.set_span_attribute("exp_sub_path", exp_sub_path[0])
    exp_sub_path = exp_sub_path[0]
else:
    exp_sub_path = ""
selected_experiences = self.load_experience(query=query, sub_path=exp_sub_path)
```
Other roles that are not responsible for setting the experience subdirectory can ignore the attachment.
In this way, we can set the experience subdirectory dynamically based on the task type.

The signal is maintained at the session level, which means that the signal is valid for the current session.
The value of the signal can be changed by sending another signal with the same attachment type.
Note that after the signal is set, all roles will keep receiving the signal until the session ends.
So, it is each role's responsibility to implement the logic to handle duplicate signals.

## Conclusion

In this blog post, we have discussed how to select experiences in TaskWeaver.
We have static experience selection by configuring the experience directory for each role.
To enable dynamic experience selection, we have introduced the concept of experience subdirectory and signal attachment.
