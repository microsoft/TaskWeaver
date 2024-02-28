# Code Execution

TaskWeaver is a code-first agent framework, which means that it always converts the user request into code 
and executes the code to generate the response. In our current implementation, we use a Jupyter Kernel
to execute the code. We choose Jupyter Kernel because it is a well-established tool for interactive computing
and it supports many programming languages.

## Two Modes of Code Execution

TaskWeaver supports two modes of code execution: `SubProcess` and `Container`. 
The `SubProcess` mode is the default mode. The key difference between the two modes is that the `Container` mode
executes the code in a Docker container, which provides a more secure environment for code execution, while
the `SubProcess` mode executes the code as a subprocess of the TaskWeaver process.
As a result, in the `SubProcess` mode, if the user has malicious intent, the user could potentially
instruct TaskWeaver to execute harmful code on the host machine. In addition, the LLM could also generate
harmful code, leading to potential security risks.

>💡We recommend using the `Container` mode for code execution, especially when the usage of the agent
is open to untrusted users. In the `Container` mode, the code is executed in a Docker container, which is isolated
from the host machine. 

## How to Configure the Code Execution Mode

To configure the code execution mode, you need to set the `execution_service.kernel_mode` parameter in the
`taskweaver_config.json` file. The value of the parameter could be `SubProcess` or `Container`. The default value
is `SubProcess`.

TaskWeaver supports the `SubProcess` mode without any additional setup. However, to use the `Container` mode,
there are a few prerequisites:

- Docker is installed on the host machine.
- A Docker image is built and available on the host machine for code execution.
- The `execution_service.kernel_mode` parameter is set to `Container` in the `taskweaver_config.json` file.

Once the code repository is cloned to your local machine, you can build the Docker image
by running the following command in the root directory of the code repository:

```bash
cd ces_container

# based on your OS
./build.ps1 # for Windows
./build.sh # for Linux or macOS
```

After the Docker image is built, you can run `docker images` to check if a Docker image 
named `executor_container` is available. 
If the prerequisite is met, you can now run TaskWeaver in the `Container` mode.



