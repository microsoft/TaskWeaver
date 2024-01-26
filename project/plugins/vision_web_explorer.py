import base64
import json
import time
from io import BytesIO
from typing import Dict, List, Tuple

import requests

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

from taskweaver.plugin import Plugin, register_plugin


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
            chrome_options.add_argument("--ignore-certificate-errors")
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

    def open(self, url: str):
        self.driver.get(url)

    def save_screenshot(self, filename: str):
        self.driver.save_screenshot(filename + "_no_labels.png")

        script = """
        (function() {
            function removeDataLabelNumberAttributes() {
              const elementsWithAttribute = document.querySelectorAll('[data-label-number]');

              elementsWithAttribute.forEach(el => {
                el.removeAttribute('data-label-number');
              });
            }
            removeDataLabelNumberAttributes();

            const elementSelectors = {
              'a': 'a[href]:not([href^="#"]):not([tabindex="-1"])',
              'button': 'button:not([disabled]):not([tabindex="-1"])',
              'input': 'input:not([type="hidden"]):not([disabled]):not([readonly]):not([tabindex="-1"])',
              'select': 'select:not([disabled]):not([tabindex="-1"])',
              'textarea': 'textarea:not([disabled]):not([readonly]):not([tabindex="-1"])',
              'role-button': '[role="button"]:not([disabled]):not([tabindex="-1"])',
              'role-link': '[role="link"]:not([tabindex="-1"])',
              'role-menu': 'ul[role="menu"] > li',
              'role-tab': '[role="tab"]:not([tabindex="-1"])',
              'role-combobox': '[role="combobox"]:not([tabindex="-1"])',
              'role-listbox': '[role="listbox"]:not([tabindex="-1"])',
              'role-option': '[role="option"]:not([tabindex="-1"])',
              'role-switch': '[role="switch"]:not([tabindex="-1"])',
              'contenteditable': '[contenteditable]:not([tabindex="-1"])'
            };

            const colors = {
              'a': 'blue',
              'button': 'green',
              'input': 'orange',
              'select': 'red',
              'textarea': 'purple',
              'role-button': 'pink',
              'role-link': 'cyan',
              'role-menu': 'skyblue',
              'role-tab': 'brown',
              'role-combobox': 'magenta',
              'role-listbox': 'lime',
              'role-option': 'darkblue',
              'role-switch': 'olive',
              'contenteditable': 'teal'
            };


            function createLabelElement(index, rect, color) {
              const labelElement = document.createElement('div');
              labelElement.textContent = index;
              labelElement.style.position = 'absolute';
              labelElement.style.left = `${rect.left + window.scrollX}px`; // Add scrollX position
              labelElement.style.top = `${rect.top + rect.height / 2 - 6 + window.scrollY}px`; // Add scrollY position
              labelElement.style.background = color;
              labelElement.style.color = 'white';
              labelElement.style.padding = '2px';
              labelElement.style.borderRadius = '4px';
              labelElement.style.fontSize = '12px';
              labelElement.style.zIndex = '10000';
              labelElement.setAttribute('label-element-number', index.toString());

              return labelElement;
            }

            function isElementInViewport(el) {
              const rect = el.getBoundingClientRect();
              const windowHeight = (window.innerHeight || document.documentElement.clientHeight);
              const windowWidth = (window.innerWidth || document.documentElement.clientWidth);

              return (
                rect.top < windowHeight && // Check if the top edge is below the viewport's top
                rect.left < windowWidth && // Check if the left edge is inside the viewport's right
                rect.bottom > 0 && // Check if the bottom edge is above the viewport's bottom
                rect.right > 0 // Check if the right edge is inside the viewport's left
              );
            }

            const elements = [];
            let index = 0;

            Object.keys(elementSelectors).forEach(type => {
              Array.from(document.querySelectorAll(elementSelectors[type]))
                .filter(el => {
                  const style = window.getComputedStyle(el);
                  return style.display !== 'none' && style.visibility !== 'hidden' && isElementInViewport(el);
                })
                .forEach(el => {
                  const rect = el.getBoundingClientRect();
                  const color = colors[type];
                  const labelElement = createLabelElement(index, rect, color);
                el.setAttribute('data-label-number', index.toString());
                document.body.appendChild(labelElement);
                elements.push({ element: el, type: type });
                index++;
              });
          });
        })();
        """

        # Execute the JavaScript to add labels to the page
        self.driver.execute_script(script)

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
        print("Performing action: ", action)
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
        elif "done" in action:
            pass
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
    prompt: str = """You need to help a user do this task: {objective}

    ## Available actions
    Your available actions are:
    - open a URL, e.g., {{"open": "https://www.google.com", "description": "what and why you want to open"}}
    - click on a web element, e.g., {{"click": "123", "description": "what and why you want to click"}}
    - type a message, e.g., {{"type": "123", "text": "hello world", "description": "what you want to type"}}
    - view the content on the current page, e.g., {{"view": "what you want to see", "description": "what you see from the image"}}
    - scroll up, e.g., {{"scroll_up": "", "description": "why you want to scroll up"}}
    - scroll down, e.g., {{"scroll_down": "", "description": "why you want to scroll down"}}
    - refresh the page, e.g., {{"refresh": "", "description": "why you want to refresh"}}
    - go back to the previous page when you are stuck, e.g., {{"back": "", "description": "why you want to go back"}}
    - go forward to the next page, e.g., {{"forward": "", "description": "why you want to go forward"}}
    - find key words on the page and goto the first one, e.g., {{"find": "Christmas", "description": "why you want to find"}}
    - take a screenshot so that you can check the action result, e.g., {{"screenshot": "", "description": "why you want to take a screenshot"}}
    - done if the task is done, e.g., {{"done": "", "description": "why you think it is done and what is the result"}}
    - stop if you need to get input from the user, e.g., {{"stop": "information you need from user", "description": "why you want to stop"}}
    - press enter on the active element, e.g., {{"enter": "", "description": "why you want to press enter"}}

    ## On the response format
    You can plan multiple actions at once.
    For example, you can type "Wikipedia" in the search box and click the search button after that.
    You must pack all the actions into a JSON list. The actions will be taken following the order of the list.
    You must respond in JSON only with no other fluff or bad things will happen.
    The JSON keys must ONLY be one of the above actions, following the examples above.
    Do not return the JSON inside a code block or anything else like ``` or ```json.

    ## Previous actions
    To achieve the objective, you have already taken the following actions:
    {previous_action}

    ## On screenshot
    When you take a screenshot, you will see an image. This is the only way you can see the web page.
    The typical interaction is to choose an action, then take screenshot to check the result, and so on.
    If you did not take a screenshot, you will not be able to see the web page and you will not be able to take any actions further.
    This image is the current state of the page which consists of two images, one with labeling (right) and the other without labeling (left).
    The label is to help you identify the web elements on the page.
    Each label is a number at the left upper corner of the web element.
    You can refer to the image without labeling to see what the web elements are without blocking the view of the page.
    You must first take a screenshot before planning any interactions (click and type) with the elements because they all require a element label only available on the screenshot.
    You can take only one screenshot at each step. Otherwise, you will get confused.

    ## On done
    You can plan a "done" action to indicate that the objective is fulfilled.
    If the objective is to find certain information on the page, you need to put the information in the "done" action.
    Otherwise, the user will not know what you have found.
    Make sure you fill meaningful information in the "done" action.

    ## Examples

    ### Example 1
    objective: Search iphone on google
    step 1 plan:
    [{{"open": "https://www.google.com", "description": "open the google for search"}}, {{"screenshot":"", "description":"view the search page for planning next actions"}}]
    step 2 plan:
    [{{"type": "123", "text": "iphone", "description": "type the key words into the search text box"}}, {{"click": "232", "description": "click the search button to trigger the search process"}}, {{"screenshot":"", "description":"view the search page for planning next actions"}}]
    step 3 plan:
    [{{"view": "I can see the search result of iphone in google", "description": "I see the results"}}, {{"screenshot":"", "description":"view the search page for planning next actions"}}]
    step 4 plan:
    [{{"done": "The objective is fulfilled. I can see the search result of iphone in google."}}]

    ### Example 2
    objective: On Microsoft's Wikipedia page, there is a image of "Five year history graph". What is the price range of Microsoft in that image?
    step 1 plan:
    [{{"open": "https://google.com", "description": "open the google for search"}}, {{"screenshot":"", "description":"view the search page for planning next actions"}}]
    step 2 plan:
    [{{"type": "123", "text": "Microsoft Wikipedia", "description": "type the key words into the search text box"}}, {{"click": "232", "description": "click the search button to trigger the search process"}}, {{"screenshot":"", "description":"view the search page for planning next actions"}}]
    step 3 plan:
    [{{"click": "123", "description": "click the Wikipedia link to go to the Wikipedia page"}}, {{"screenshot":"", "description":"view the search page for planning next actions"}}]
    step 4 plan:
    [{{"view": "I can see the Wikipedia page of Microsoft", "description": "I want to see the Wikipedia page"}}, {{"screenshot":"", "description":"view the search page for planning next actions"}}]
    step 5 plan:
    [{{"scroll_down": "", "description": "scroll down to see the image"}}, {{"screenshot":"", "description":"view the search page for planning next actions"}}]
    step 6 plan:
    [{{"scroll_down": "", "description": "scroll down to see the image again"}}, {{"screenshot":"", "description":"view the search page for planning next actions"}}]
    step 7 plan:
    [{{"view": "I can see the image of Five year history graph", "description": "The price range is between 15$ to 37$"}}, {{"screenshot":"", "description":"view the search page for planning next actions"}}]
    step 8 plan:
    [{{"done": "The objective is fulfilled. The price range is between 15$ to 37$."}}]
    """

    def __init__(self, api_key: str, endpoint: str, driver: SeleniumDriver):
        self.gpt4v_key = api_key
        self.gpt4v_endpoint = endpoint

        self.headers = {
            "Content-Type": "application/json",
            "api-key": api_key,
        }
        self.driver = driver
        self.previous_actions = []
        self.step = 0

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
        additional_info: str = None,
        save_screenshot: bool = True,
    ) -> Tuple[str, str]:
        # always take a screenshot at the beginning
        screenshot_action = [
            {
                "screenshot": "",
                "description": "take a screenshot to check the current status of the page",
            },
        ]
        plan = screenshot_action

        if additional_info is None:
            # this is a fresh start
            self.step = 0
            self.driver.open("https://www.google.com")
            self.previous_actions = [str(screenshot_action)]
        else:
            # this is a continuation
            self.previous_actions.append(f"User input: '{additional_info}'")

        while True:
            screenshot, mapping = self.driver.perform_actions(plan)
            if screenshot is None:
                print("No screenshot is taken. Take a screenshot in addition.")
                screenshot, mapping = self.driver.perform_actions(screenshot_action)
                if save_screenshot:
                    screenshot.save(f"screenshot{self.step}.png")
                self.previous_actions.append(str(screenshot_action))
                self.step += 1
            else:
                if save_screenshot:
                    screenshot.save(f"screenshot{self.step}.png")

            plan = self.get_actions(
                screenshot=screenshot,
                request=objective,
                mapping=mapping,
                prev_actions=self.previous_actions,
            )
            print("Plan:", plan)

            is_done = False
            done_message = None
            is_stop = False
            stop_message = None
            for action in plan:
                if "done" in action:
                    is_done = True
                    done_message = action["done"]
                    break
                if "stop" in action:
                    is_stop = True
                    stop_message = action["stop"]
                    break

            if is_done:
                print("Done!")
                return done_message, str(self.previous_actions)

            self.previous_actions.append(str(plan))
            if is_stop:
                print("Stop!")
                return f"Please enter information on '{stop_message}': ", str(self.previous_actions)

            self.step += 1
            if self.step > 10:
                print("Too many steps. Stop!")
                return (
                    "Failed to achieve the objective. Too many steps. "
                    "Could you please split the objective into smaller ones?"
                ), str(self.previous_actions)


@register_plugin
class VisionWebBrowser(Plugin):
    vision_planner: VisionPlanner = None

    def _init(self):
        driver = None
        try:
            GPT4V_KEY = self.config.get("api_key")
            GPT4V_ENDPOINT = self.config.get("endpoint")
            driver = SeleniumDriver(
                chrome_driver_path=self.config.get("chrome_driver_path"),
                chrome_executable_path=self.config.get("chrome_executable_path", None),
                mobile_emulation=False,
            )
            self.vision_planner = VisionPlanner(
                api_key=GPT4V_KEY,
                endpoint=GPT4V_ENDPOINT,
                driver=driver,
            )
        except Exception as e:
            if driver is not None:
                driver.quit()
            raise Exception(f"Failed to initialize the plugin due to: {e}")

    def __call__(self, request: str, additional_info: str = None):
        if self.vision_planner is None:
            self._init()
        try:
            done_message = self.vision_planner.get_objective_done(
                request,
                additional_info,
            )
        except Exception as e:
            print(e)
            done_message = "Failed to achieve the objective. Please check the log for more details."

        return done_message
