from typing import List, Tuple


class PromptUtil:
    DELIMITER_TEMPORAL: Tuple[str, str] = ("{{DELIMITER_START_TEMPORAL}}", "{{DELIMITER_END_TEMPORAL}}")

    @staticmethod
    def wrap_text_with_delimiter(text, delimiter: Tuple[str, str]) -> str:
        """Wrap the provided text with the specified start and end delimiters."""
        return f"{delimiter[0]}{text}{delimiter[1]}"

    @staticmethod
    def get_all_delimiters() -> List[Tuple[str, str]]:
        """Get all the delimiters."""
        return [getattr(PromptUtil, attr) for attr in dir(PromptUtil) if attr.startswith("DELIMITER_")]

    @staticmethod
    def remove_parts(text: str, delimiter: Tuple[str, str]) -> str:
        """Remove the parts of the text that are wrapped by the specified delimiters."""
        while True:
            # Find the start of the temporal part
            start_index = text.find(delimiter[0])
            # Find the end of the temporal part
            end_index = text.find(delimiter[1], start_index + len(delimiter[0]))

            # Check if both markers are present
            if start_index != -1 and end_index != -1:
                # Ensure that the start marker comes before the end marker
                if start_index < end_index:
                    # Remove the temporal part including the markers
                    text = text[:start_index] + text[end_index + len(delimiter[1]) :]
                else:
                    break
            elif start_index == -1 and end_index == -1:
                # No more markers found, break the loop
                break
            else:
                # One of the markers is found without the other
                break
        return text

    @staticmethod
    def remove_delimiter(text: str, delimiter: Tuple[str, str]):
        """Remove the specified delimiter from the text."""
        text = text.replace(delimiter[0], "")
        text = text.replace(delimiter[1], "")
        return text

    @staticmethod
    def remove_all_delimiters(text: str) -> str:
        """Remove all the delimiters from the text."""
        for delimiter in PromptUtil.get_all_delimiters():
            text = PromptUtil.remove_delimiter(text, delimiter)
        return text
