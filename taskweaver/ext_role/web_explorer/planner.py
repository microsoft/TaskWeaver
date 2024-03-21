import base64
import json
from io import BytesIO

import requests

from taskweaver.ext_role.web_explorer.driver import SeleniumDriver
from taskweaver.memory.attachment import AttachmentType
from taskweaver.module.event_emitter import PostEventProxy


def encode_and_resize(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return encoded_image


class VisionPlanner:
    def __init__(self, api_key: str, endpoint: str, driver: SeleniumDriver, prompt: str = None):
        self.gpt4v_key = api_key
        self.gpt4v_endpoint = endpoint

        self.headers = {
            "Content-Type": "application/json",
            "api-key": api_key,
        }
        self.driver = driver
        self.previous_actions = []
        self.step = 0
        self.prompt = prompt

    def get_actions(
        self,
        screenshot,
        request: str,
        prev_actions: list = None,
        mapping: dict = None,
    ):
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": self.prompt.format(
                                objective=request,
                                previous_action="\n".join(prev_actions) if prev_actions else "None",
                            ),
                        },
                    ],
                },
            ],
            "max_tokens": 300,
        }

        if screenshot is not None:
            payload["messages"][0]["content"].append(
                {
                    "type": "text",
                    "text": "The following is the screenshot after taking the previous actions:",
                },
            )
            payload["messages"][0]["content"].append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encode_and_resize(screenshot)}",
                    },
                },
            )
            mapping_str = "\n".join([f"label_number={k}: element_info={v}" for k, v in mapping.items()])
            payload["messages"][0]["content"].append(
                {
                    "type": "text",
                    "text": f"The interactable elements on this web page are:\n"
                    f"{mapping_str}\n\n"
                    f"What are your next actions? If you don't know what to do next or you are not confident, "
                    "just plan a 'stop' action and explain what you need from the user."
                    "Make sure you answer in JSON format only, or very bad things will happen."
                    "Make sure you have screenshot at the end of your plan.",
                },
            )

        try:
            response = requests.post(self.gpt4v_endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            json_response = response.json()
        except requests.RequestException as e:
            raise SystemExit(f"Failed to make the request. Error: {e}")

        return json.loads(json_response["choices"][0]["message"]["content"])

    def get_objective_done(
        self,
        objective: str,
        post_proxy: PostEventProxy,
        save_screenshot: bool = True,
    ):
        # this is a fresh start
        if self.step == 0:
            self.driver.open("https://www.google.com")

        # always take a screenshot at the beginning
        screenshot_action = [
            {
                "screenshot": "",
                "description": "take a screenshot to check the current status of the page",
            },
        ]
        plan = screenshot_action
        self.previous_actions.append(str(screenshot_action))

        inner_step = 0
        while True:
            post_proxy.update_attachment(
                message=json.dumps(plan, indent=2),
                type=AttachmentType.web_exploring_plan,
            )
            screenshot, mapping = self.driver.perform_actions(plan)
            if screenshot is None:
                post_proxy.update_attachment(
                    message=json.dumps(screenshot_action, indent=2),
                    type=AttachmentType.web_exploring_plan,
                )
                screenshot, mapping = self.driver.perform_actions(screenshot_action)
                if save_screenshot:
                    screenshot.save(f"screenshot{self.step + inner_step}.png")
                self.previous_actions.append(str(screenshot_action))
                inner_step += 1
            else:
                if save_screenshot:
                    screenshot.save(f"screenshot{self.step + inner_step}.png")

            plan = self.get_actions(
                screenshot=screenshot,
                request=objective,
                mapping=mapping,
                prev_actions=self.previous_actions,
            )

            self.previous_actions.append(str(plan))

            is_stop = False
            stop_message = None
            for action in plan:
                if "stop" in action:
                    is_stop = True
                    stop_message = action["stop"]
                    break

            if is_stop:
                post_proxy.update_message(
                    f"The previous task is stopped.\n"
                    f"The actions taken are:\n{self.previous_actions}.\n"
                    f"The current link is: {self.driver.driver.current_url}.\n"
                    f"The message is: {stop_message}",
                )
                break

            inner_step += 1
            if inner_step > 10:
                post_proxy.update_message(
                    f"The actions taken are:\n{self.previous_actions}.\n"
                    "Failed to achieve the objective. Too many steps. "
                    "Could you please split the objective into smaller subtasks?",
                )

        self.step += inner_step
