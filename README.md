# TaskWeaver

A framework that make it easy to craft AI copilots capable of understanding 
and executing complex tasks based on Python code interpretation and plugin orchestration. 

**Highlighted Features**

- [x] **Rich data structure** - TaskWeaver allows you to work with rich data 
    structures in Python, such as DataFrames, instead of having to work with 
    text strings.
- [x] **Customized algorithms** - TaskWeaver allows you to encapsulate your 
    own algorithms into plugins (in the form of Python functions), 
    and orchestrate them to achieve complex tasks.
- [x] **Incorporating domain-specific knowledge** - TaskWeaver is designed to 
    be easily incorporating domain-specific knowledge, such as the knowledge 
    of execution flow, to improve the reliability of the AI copilot.
- [x] **Easy extension** - TaskWeaver is designed to be easily extended to accomplish 
    more complex tasks. You can create multiple AI copilots to
    act in different roles, and orchestrate them to achieve complex tasks.
- [x] **Robust code execution** - TaskWeaver is designed to be robust in running the generated code.
    It can handle unexpected situations, such as the failure of during code 
    execution, and recover from them.
- [x] **Easy to use** - TaskWeaver is designed to be easy to use. 
    We provide a set of sample plugins and a tutorial to help you get started.
    Users can easily create their own plugins based on the sample plugins.
    TaskWeaver offers an open-box experience, allowing users to run a service immediately after installation.
- [x] **Easy to debug** - TaskWeaver is designed to be easy to debug. 
    We have detailed logs to help you understand what is going on during calling the LLM, 
    the code generation, and execution process.
- [x] **Security consideration** - TaskWeaver supports a basic session management to keep
    different users' data separate. The code execution is separated into different processes
    in order not to interfere with each other.

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
