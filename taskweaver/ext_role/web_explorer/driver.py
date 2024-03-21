import time
from typing import Dict, List

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select


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
        chrome_options = webdriver.ChromeOptions()
        if mobile_emulation:
            mobile_emulation = {
                "deviceMetrics": {"width": 375, "height": 812, "pixelRatio": 3.0},
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, "
                "like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
            }
            chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
            chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_argument("--log-level=OFF")
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--ignore-ssl-errors")
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
