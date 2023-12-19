# Session

`session` is the entrance of TaskWeaver. 
It is responsible for the communication between the user and TaskWeaver.
You can refer to [taskweaver_as_a_lib](taskweaver_as_a_lib.md) to see how to setup a TaskWeaver session and start chatting with TaskWeaver.


## Session Configration
- `max_internal_chat_round_num`: the maximum number of internal chat rounds between Planner and Code Interpreter. 
  If the number of internal chat rounds exceeds this number, the session will be terminated. 
  The default value is `10`.
- `code_interpreter_only`: allow users to directly communicate with the Code Interpreter.
   In this mode, users can only send messages to the Code Interpreter and receive messages from the Code Interpreter.
   Here is an example:
`````bash
 =========================================================
 _____         _     _       __
|_   _|_ _ ___| | _ | |     / /__  ____ __   _____  _____
  | |/ _` / __| |/ /| | /| / / _ \/ __ `/ | / / _ \/ ___/
  | | (_| \__ \   < | |/ |/ /  __/ /_/ /| |/ /  __/ /
  |_|\__,_|___/_|\_\|__/|__/\___/\__,_/ |___/\___/_/
=========================================================
TaskWeaver: I am TaskWeaver, an AI assistant. To get started, could you please enter your request?
Human: generate 10 random numbers
>>> [PYTHON]tarting...      <=�=>     >
import numpy as np
random_numbers = np.random.rand(10)
random_numbers
>>> [VERIFICATION]
NONE
>>> [STATUS]tarting...         <=�=>  
SUCCESS
>>> [RESULT]
The execution of the generated python code above has succeeded

The result of above Python code after execution is:
array([0.09918602, 0.68732778, 0.44413814, 0.4756623 , 0.48302334,
       0.8286594 , 0.80994359, 0.35677263, 0.45719317, 0.68240194])
>>> [CODEINTERPRETER->PLANNER]
The following python code has been executed:
```python
import numpy as np
random_numbers = np.random.rand(10)
random_numbers
```

The execution of the generated python code above has succeeded

The result of above Python code after execution is:
array([0.09918602, 0.68732778, 0.44413814, 0.4756623 , 0.48302334,
       0.8286594 , 0.80994359, 0.35677263, 0.45719317, 0.68240194])
TaskWeaver: The following python code has been executed:
```python
import numpy as np
random_numbers = np.random.rand(10)
random_numbers
\```

The execution of the generated python code above has succeeded

The result of above Python code after execution is:
array([0.09918602, 0.68732778, 0.44413814, 0.4756623 , 0.48302334,
       0.8286594 , 0.80994359, 0.35677263, 0.45719317, 0.68240194])
`````