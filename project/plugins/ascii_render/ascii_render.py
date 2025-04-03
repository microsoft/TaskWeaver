from taskweaver.plugin import Plugin, register_plugin


@register_plugin
class AsciiRenderPlugin(Plugin):
    def __call__(self, text: str):
        try:
            import pyfiglet
        except ImportError:
            raise ImportError("Please install pyfiglet first.")

        ASCII_art_1 = pyfiglet.figlet_format(text, font="isometric1")
        result = ASCII_art_1

        return result


if __name__ == "__main__":
    from taskweaver.plugin.context import temp_context

    with temp_context() as temp_ctx:
        render = AsciiRenderPlugin(name="ascii_render", ctx=temp_ctx, config={})
        print(render(text="hello world!"))
