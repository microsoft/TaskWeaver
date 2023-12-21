# Library

If you want to use TaskWeaver as a library, you can refer to the following code example:

```python
from taskweaver.app.app import TaskWeaverApp

# This is the folder that contains the taskweaver_config.json file and not the repo root. Defaults to "./project/"
app_dir = "./project/"
app = TaskWeaverApp(app_dir=app_dir)
session = app.get_session()

user_query = "hello, what can you do?"
response_round = session.send_message(user_query,
                                      event_handler=lambda _type, _msg: print(f"{_type}:\n{_msg}"))
print(response_round.to_dict())
```
**Note:**
- `event_handler`: a callback function that is utilized to display the internal planning and execution steps of TaskWeaver.
  It takes two arguments: the message type (e.g., `plan`) and the message body.
- `response_round`: the response from TaskWeaver. which is an object of the `Round` class. 
  An example of the `Round` object is shown below:
```json
{
    "id": "round-20231201-043134-218a2681",
    "user_query": "hello, what can you do?",
    "state": "finished",
    "post_list": [
        {
            "id": "post-20231201-043134-10eedcca",
            "message": "hello, what can you do?",
            "send_from": "User",
            "send_to": "Planner",
            "attachment_list": []
        },
        {
            "id": "post-20231201-043141-86a2aaff",
            "message": "I can help you with various tasks, such as counting rows in a data file, detecting anomalies in a dataset, searching for products on Klarna, summarizing research papers, and pulling data from a SQL database. Please provide more information about the task you want to accomplish, and I'll guide you through the process.",
            "send_from": "Planner",
            "send_to": "User",
            "attachment_list": [
                {
                    "id": "atta-20231201-043141-6bc4da86",
                    "type": "init_plan",
                    "content": "1. list the available functions"
                },
                {
                    "id": "atta-20231201-043141-6f29f6c9",
                    "type": "plan",
                    "content": "1. list the available functions"
                },
                {
                    "id": "atta-20231201-043141-76186c7a",
                    "type": "current_plan_step",
                    "content": "1. list the available functions"
                }
            ]
        }
    ]
}
```
