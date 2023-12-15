from taskweaver.plugin import Plugin, register_plugin


@register_plugin
class TellJoke(Plugin):
    def __call__(self, context: str):
        # Define the API endpoint and parameters
        return " Why don't cats play poker in the jungle? Too many cheetahs!"
