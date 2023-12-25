from taskweaver.plugin import Plugin, register_plugin


@register_plugin
class TellJoke(Plugin):
    def __call__(self, lan: str = "en"):
        try:
            import pyjokes
        except ImportError:
            raise ImportError("Please install pyjokes first.")

        # Define the API endpoint and parameters
        return pyjokes.get_joke(language=lan, category="neutral")
