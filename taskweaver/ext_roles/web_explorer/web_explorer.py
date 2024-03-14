import base64
import json
import os
import time
from io import BytesIO
from typing import Dict, List

import requests
from injector import inject

from taskweaver.config.module_config import ModuleConfig
from taskweaver.logging import TelemetryLogger
from taskweaver.memory import Memory, Post
from taskweaver.memory.attachment import AttachmentType
from taskweaver.module.event_emitter import PostEventProxy, SessionEventEmitter
from taskweaver.role import Role
from taskweaver.utils import read_yaml

try:
    from PIL import Image
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.select import Select
except ImportError:
    raise ImportError("Please install selenium first.")


# Function to encode the image
def encode_and_resize(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return encoded_image


class SeleniumDriver:
    def __init__(
        self,
        mobile_emulation: bool = True,
        chrome_driver_path: str = None,
        chrome_executable_path: str = None,
        action_delay: int = 5,
        js_script: str = None,
    ):
        # Set up Chrome options
        chrome_options = Options()
        if mobile_emulation:
            mobile_emulation = {
                "deviceMetrics": {"width": 375, "height": 812, "pixelRatio": 3.0},
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, "
                "like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
            }
            chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
            chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
            chrome_options.add_argument("--ignore--errors")
            chrome_options.add_argument("--log-level=OFF")
            chrome_options.add_argument("--allow-insecure-localhost")
            chrome_options.add_argument("--log-level=3")
            if chrome_executable_path is not None:
                chrome_options.binary_location = chrome_executable_path

            # Set up the service object with the specified path to chromedriver
        service = Service(executable_path=chrome_driver_path)

        # Set up the driver with the specified service
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        self.action_delay = action_delay
        self.js_script = js_script

    def open(self, url: str):
        self.driver.get(url)

    def save_screenshot(self, filename: str):
        self.driver.save_screenshot(filename + "_no_labels.png")

        # Execute the JavaScript to add labels to the page
        self.driver.execute_script(self.js_script)

        self.driver.save_screenshot(filename + "_with_labels.png")

        # Find all elements with a 'data-label-number' attribute
        elements_with_label_number = self.driver.find_elements(by="css selector", value="[data-label-number]")

        # Initialize a dictionary to store the mapping
        label_element_mapping = {}

        def extract_basic_info(el):
            element_info = {}
            element_type = el.tag_name  # Might be None if the attribute is not present
            element_info["type"] = element_type

            if len(el.accessible_name) > 0:
                element_info["name"] = el.accessible_name

            if el.text != el.accessible_name:
                element_info["text"] = el.text

            if element_type == "select":
                select_element = Select(el)
                element_info["options"] = [option.text for option in select_element.options]
            elif element_type == "input":
                element_info["value"] = el.get_attribute("value")
                element_info["placeholder"] = el.get_attribute("placeholder")
            elif element_type == "button":
                element_info["enabled"] = el.is_enabled()
            # elif element_type == "a":
            #     element_info["href"] = element.get_attribute("href")

            # Get common attributes
            # element_info["id"] = el.get_attribute("id")
            # element_info["class"] = el.get_attribute("class")

            return element_info

        # Iterate through the elements and extract the required information
        for element in elements_with_label_number:
            # Extract the label number from the 'data-label-number' attribute
            label_number = element.get_attribute("data-label-number")

            try:
                # Extract the element information
                element_info = extract_basic_info(element)

                # Add the mapping to the dictionary
                label_element_mapping[label_number] = element_info
                # print(f"Label number: {label_number}, Element info: {element_info}")
            except Exception as e:
                print(e)

        remove_labels_script = """
        (function() {
            var labels = document.querySelectorAll('div[label-element-number]');
            labels.forEach(function(label) {
              label.parentNode.removeChild(label);
            });
        })();
        """
        self.driver.execute_script(remove_labels_script)

        # Open the two images
        image1 = Image.open(filename + "_no_labels.png")  # 'screenshot_no_labels.png'
        image2 = Image.open(filename + "_with_labels.png")  # 'screenshot_with_labels.png'

        # Define the width and color of the border
        border_width = 10  # in pixels
        border_color = (0, 0, 0)  # black

        # Calculate dimensions for the new image
        total_width = image1.width + image2.width + border_width
        max_height = max(image1.height, image2.height)

        # Create a new blank image with the appropriate size
        new_image = Image.new("RGB", (total_width, max_height), color=border_color)

        # Paste image1 and image2 into the new image
        new_image.paste(image1, (0, 0))
        new_image.paste(image2, (image1.width + border_width, 0))

        return new_image, label_element_mapping

    def quit(self):
        self.driver.quit()

    def click(self, element_number: int):
        element = self.driver.find_element(
            by="css selector",
            value=f'[data-label-number="{element_number}"]',
        )
        self.driver.execute_script("arguments[0].click();", element)

    def type(self, element_number: int, text: str):
        element = self.driver.find_element(
            by="css selector",
            value=f'[data-label-number="{element_number}"]',
        )
        self.driver.execute_script(f"arguments[0].value = '{text}';", element)

    def scroll_half_page_down(self):
        self.driver.execute_script("window.scrollBy(0, window.innerHeight / 2);")

    def scroll_half_page_up(self):
        self.driver.execute_script("window.scrollBy(0, -window.innerHeight / 2);")

    def select(self, element_number: int, value: str):
        element = self.driver.find_element(
            by="css selector",
            value=f'[data-label-number="{element_number}"]',
        )
        select = Select(element)
        select.select_by_visible_text(value)

    def get_text(self, element_number: int):
        element = self.driver.find_element(
            by="css selector",
            value=f'[data-label-number="{element_number}"]',
        )
        return element.text

    def refresh(self):
        self.driver.refresh()
        self.driver.implicitly_wait(3)

    def go_forward(self):
        self.driver.forward()

    def go_backward(self):
        self.driver.back()

    def find(self, text: str):
        elements = self.driver.find_elements(By.TAG_NAME, "p")
        elements.extend(self.driver.find_elements(By.TAG_NAME, "h1"))
        elements.extend(self.driver.find_elements(By.TAG_NAME, "h2"))
        elements.extend(self.driver.find_elements(By.TAG_NAME, "h3"))
        elements.extend(self.driver.find_elements(By.TAG_NAME, "li"))
        elements.extend(self.driver.find_elements(By.TAG_NAME, "a"))
        elements.extend(self.driver.find_elements(By.TAG_NAME, "span"))
        elements.extend(self.driver.find_elements(By.TAG_NAME, "div"))
        # ... add other tags as needed

        # Search for the keyword in elements
        for element in elements:
            if text.lower() in element.text.lower():
                print("Keyword found: ", element.text)
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                break

    def press_enter(self):
        # Find the currently focused element
        focused_element = self.driver.switch_to.active_element

        # Press Enter
        focused_element.send_keys(Keys.ENTER)

    def perform_action(self, action: Dict[str, str]):
        # print("Performing action: ", action)
        screenshot, mapping = None, None
        if "click" in action:
            self.click(int(action["click"]))
        elif "open" in action:
            self.open(action["open"])
        elif "type" in action:
            self.type(int(action["type"]), action["text"])
        elif "scroll_up" in action:
            self.scroll_half_page_up()
        elif "scroll_down" in action:
            self.scroll_half_page_down()
        elif "refresh" in action:
            self.refresh()
        elif "forward" in action:
            self.go_forward()
        elif "backward" in action:
            self.go_backward()
        elif "select" in action:
            self.select(int(action["select"]), action["value"])
        elif "find" in action:
            self.find(action["find"])
        elif "screenshot" in action:
            screenshot, mapping = self.save_screenshot(action["screenshot"])
        elif "stop" in action:
            pass
        elif "enter" in action:
            self.press_enter()

        time.sleep(self.action_delay)

        return screenshot, mapping

    def perform_actions(self, actions: List[Dict[str, str]]):
        screenshot, mapping = None, None
        for action in actions:
            _screenshot, _mapping = self.perform_action(action)
            if _screenshot is not None:
                screenshot, mapping = _screenshot, _mapping
        return screenshot, mapping


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


class WebExplorerConfig(ModuleConfig):
    def _configure(self):
        self._set_name("web_explorer")
        self.config_file_path = self._get_str("prompt_file_path", "web_explorer_config.yaml")


class WebExplorer(Role):
    @inject
    def __init__(
        self,
        config: WebExplorerConfig,
        logger: TelemetryLogger,
        event_emitter: SessionEventEmitter,
    ):
        super().__init__(config, logger, event_emitter)

        self.logger = logger
        self.config = config
        self.vision_planner: VisionPlanner = None

    def initialize(self):
        driver = None
        try:
            config = read_yaml(self.config.config_file_path)
            GPT4V_KEY = os.environ.get("GPT4V_KEY")
            GPT4V_ENDPOINT = os.environ.get("GPT4V_ENDPOINT")
            driver = SeleniumDriver(
                chrome_driver_path=os.environ.get("CHROME_DRIVER_PATH"),
                chrome_executable_path=os.environ.get("CHROME_EXECUTABLE_PATH"),
                mobile_emulation=False,
                js_script=config["js_script"],
            )
            self.vision_planner = VisionPlanner(
                api_key=GPT4V_KEY,
                endpoint=GPT4V_ENDPOINT,
                driver=driver,
                prompt=config["prompt"],
            )
        except Exception as e:
            if driver is not None:
                driver.quit()
            raise Exception(f"Failed to initialize the plugin due to: {e}")

    def reply(self, memory: Memory, **kwargs) -> Post:
        if self.vision_planner is None:
            self.initialize()

        rounds = memory.get_role_rounds(
            role=self.alias,
            include_failure_rounds=False,
        )
        last_post = rounds[-1].post_list[-1]
        post_proxy = self.event_emitter.create_post_proxy(self.alias)
        post_proxy.update_send_to(last_post.send_from)
        try:
            self.vision_planner.get_objective_done(
                objective=last_post.message,
                post_proxy=post_proxy,
            )
        except Exception as e:
            post_proxy.update_message(
                f"Failed to achieve the objective due to {e}. " "Please check the log for more details.",
            )

        return post_proxy.end()
