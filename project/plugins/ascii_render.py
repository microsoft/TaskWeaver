from taskweaver.plugin import Plugin, register_plugin


@register_plugin
class AsciiRenderPlugin(Plugin):
    def __call__(self, text: str):
        import pyfiglet

        ASCII_art_1 = pyfiglet.figlet_format(text, font="isometric1")
        result = ASCII_art_1

        return result
