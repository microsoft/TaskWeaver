# Web UI

Please note that this Web UI is for development and testing purposes only.

Follow the instruction in [Quick Start](../quickstart.md) to clone the repository and fill in the necessary configurations.

Install the `chainlit` package by `pip install -U "chainlit<1.1.300"` if you don't have it in your environment.

:::note
Chainlit has a major update in version 1.1.300 that may cause compatibility issues. 
Please make sure you have the correct version installed.
:::

Start the service by running the following command.


```bash
# assume you are in the TaskWeaver folder
cd playground/UI/
# make sure you are in playground/UI/ folder
chainlit run app.py
```

Open the browser with http://localhost:8000 if it doesn't open automatically. 
:::info
We now support uploading files using the Web UI. 
:::
Below are some screenshots of the Web UI:
![TaskWeaver UI Screenshot 1](../../static/img/ui_screenshot_1.png)
![TaskWeaver UI Screenshot 2](../../static/img/ui_screenshot_2.png)

