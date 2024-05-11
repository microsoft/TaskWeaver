# Code Execution

>💡We have set the `container` mode as default for code execution, especially when the usage of the agent
is open to untrusted users. Refer to [Docker Security](https://docs.docker.com/engine/security/) for better understanding
of the security features of Docker. To opt for the `local` mode, you need to explicitly set the `execution_service.kernel_mode` 
parameter in the `taskweaver_config.json` file to `local`.

TaskWeaver is a code-first agent framework, which means that it always converts the user request into code 
and executes the code to generate the response. In our current implementation, we use a Jupyter Kernel
to execute the code. We choose Jupyter Kernel because it is a well-established tool for interactive computing,
and it supports many programming languages.

## Two Modes of Code Execution

TaskWeaver supports two modes of code execution: `local` and `container`. 
The `container` mode is the default mode. The key difference between the two modes is that the `container` mode
executes the code inside a Docker container, which provides a more secure environment for code execution, while
the `local` mode executes the code as a subprocess of the TaskWeaver process.
As a result, in the `local` mode, if the user has malicious intent, the user could potentially
instruct TaskWeaver to execute harmful code on the host machine. In addition, the LLM could also generate
harmful code, leading to potential security risks.



## How to Configure the Code Execution Mode

To configure the code execution mode, you need to set the `execution_service.kernel_mode` parameter in the
`taskweaver_config.json` file. The value of the parameter could be `local` or `container`. The default value
is `container`.

TaskWeaver supports the `local` mode without any additional setup. However, to use the `container` mode,
there are a few prerequisites:

- Docker is installed on the host machine.
- A Docker image is built and available on the host machine for code execution.
- The `execution_service.kernel_mode` parameter is set to `container` in the `taskweaver_config.json` file.

Once the code repository is cloned to your local machine, you can build the Docker image
by running the following command in the root directory of the code repository:

```bash
cd scripts

# based on your OS
./build_executor.ps1 # for Windows
./build_executor.sh # for Linux or macOS
```

After the Docker image is built, you can run `docker images` to check if a Docker image 
named `taskweavercontainers/taskweaver-executor` is available. 
If the prerequisite is met, you can now run TaskWeaver in the `container` mode.

After running TaskWeaver in the `container` mode, you can check if the container is running by running `docker ps`.
You should see a container of image `taskweavercontainers/taskweaver-executor` running after executing some code. 

## How to customize the Docker image for code execution

You may want to customize the Docker image for code execution to include additional packages or libraries, especially
for your developed plugins. The current Docker image for code execution only includes the dependencies specified in the `TaskWeaver/requirements.txt` file. To customize the Docker image, you need to
modify the `Dockerfile` at `TaskWeaver/docker/ces_container/Dockerfile` and rebuild the Docker image.

When you open the `Dockerfile`, you will see the following content, and you can add additional packages or libraries
by adding the corresponding `RUN` command. In this example, we add the `sentence-transformers` package to the Docker image.

```Dockerfile
FROM python:3.10-slim
...
# TODO: Install additional packages for plugins
RUN pip install --no-cache-dir --no-warn-script-location --user sentence-transformers
...
```
Then, you need to rebuild the Docker image by running the `build_executor.sh` script at `TaskWeaver/scripts/build_executor.sh` 
or `TaskWeaver/scripts/build.ps1` depending on your operating system.

```bash
cd TaskWeaver/scripts
./build_executor.sh
# or ./build_executor.ps1 if you are using Windows
```

If you have successfully rebuilt the Docker image, you can check the new image by running `docker images`.
After building the Docker image, you need to restart the TaskWeaver agent to use the new Docker image.

## Limitations of the `container` Mode

The `container` mode is more secure than the `local` mode, but it also has some limitations:

- The startup time of the `container` mode is longer than the `local` mode, because it needs to start a Docker container. 
- As the Jupyter Kernel is running inside a Docker container, it has limited access to the host machine. We are mapping the
  `project/workspace/sessions/<session_id>` directory to the container, so the code executed in the container can access the
  files in it. One implication of this is that the user cannot ask the agent to load a file from the host machine, because the
  file is not available in the container. Instead, the user needs to upload the file either using the `/upload` command in 
  the console or the `upload` button in the web interface.
- We have installed required packages in the Docker image to run the Jupyter Kernel. If the user needs to use a package that is
  not available in the Docker image, the user needs to add the package to the Dockerfile (at `TaskWeaver/ces_container/Dockerfile`) 
  and rebuild the Docker image.

## Restricting External Network Access for Docker Containers

In some cases, the agent developer may want to restrict the Docker container's access to the external network, e.g., the internet.
In other words, the agent developer only wants to run the code in the container but does not allow either 
the plugins or the generated code to access the internet.

The following approach is a common way to restrict a Docker container's access to the internet while still 
allowing inbound connections on specific ports:  
   
1. **Creating a Docker network with `enable_ip_masquerade` set to false**:  
  
   By default, Docker uses IP masquerading (a form of network address translation or NAT) to allow containers 
   to communicate with external networks with the source IP address being the host IP address. 
    When you set `enable_ip_masquerade` to false for a custom Docker network, 
    you prevent containers on that network from having their IP addresses masqueraded, effectively blocking them 
    from accessing the internet. To create such a network in Docker, you would use the following command:  
  
   ```bash  
   docker network create --opt com.docker.network.bridge.enable_ip_masquerade=false my_non_internet_network  
   ```  
  
   Any container connected to `my_non_internet_network` will not have internet access due to the disabled IP masquerade.  
    Now, you can run 
    ```bash
    docker network inspect my_non_internet_network
    ```
   and you will see an output similar to the following:
    ```json
    "Config": [
        {
            "Subnet": "172.19.0.0/16",
            "Gateway": "172.19.0.1"
        }
    ]
    ```
   This shows the subnet of the docker network, all containers connected to this network will have an IP address in this subnet.
   
2. **Establishing a rule on the host's firewall or using iptables**:  
  
   This step is about setting up rules to block outgoing traffic from the Docker network's subnet 
   to any external addresses. This adds an additional layer of security to ensure that even 
    if IP masquerade is somehow enabled or if the container finds another route, the traffic will still be blocked.  
  
   - **On a Linux host using iptables**, you might add a rule like this:  
  
     ```bash  
     iptables -I FORWARD -s <docker_network_subnet> -j DROP  
     ```  
       
     Replace `<docker_network_subnet>` with the actual subnet used by your Docker network. 
     In the previous example, the subnet is `172.19.0.0/16`. This rule drops all forwarding traffic from that subnet. 
  
   - **On a Windows host**, you would create a similar rule within the Windows Firewall 
     to block outgoing traffic from the Docker network's subnet.  
   
Keep in mind that this approach can be considered good practice if you understand the implications 
and have a specific need to isolate your container from the internet.
However, it could also complicate network troubleshooting and container communication if not managed properly. 
Always ensure you are testing these configurations in a safe environment before applying them to production systems.  
   
