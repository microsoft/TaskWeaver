# Overview

<h1 align="center">
    <img src="../static/img/logo.svg" width="45" /> TaskWeaver
</h1>

A **code-first** agent framework for seamlessly planning and executing data analytics tasks. 
This innovative framework interprets user requests through coded snippets and efficiently 
coordinates a variety of plugins in the form of functions to execute 
data analytics tasks

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
- [x] **Stateful conversation** - TaskWeaver is designed to support stateful 
    conversation. It can remember the context of the conversation and 
    leverage it to improve the user experience.
- [x] **Code verification** - TaskWeaver is designed to verify the generated code 
    before execution. It can detect potential issues in the generated code 
    and provide suggestions to fix them.
- [x] **Easy to use** - TaskWeaver is designed to be easy to use. 
    We provide a set of sample plugins and a tutorial to help you get started.
    Users can easily create their own plugins based on the sample plugins.
    TaskWeaver offers an open-box experience, allowing users to run a service immediately after installation.
- [x] **Easy to debug** - TaskWeaver is designed to be easy to debug. 
    We have detailed logs to help you understand what is going on during calling the LLM, 
    the code generation, and execution process.
- [x] **Security consideration** - TaskWeaver supports a basic session management to keep
    different users' data separate. The code execution is separated into different processes in order not to interfere with each other.
- [x] **Easy extension** - TaskWeaver is designed to be easily extended to accomplish 
    more complex tasks. You can create multiple AI copilots to
    act in different roles, and orchestrate them to achieve complex tasks.
