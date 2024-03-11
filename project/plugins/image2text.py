from taskweaver.plugin import Plugin, register_plugin

try:
    import easyocr
except ImportError:
    raise ImportError("Please install easyocr with `pip install easyocr`.")


@register_plugin
class Image2Text(Plugin):
    model = None

    def _init(self) -> None:
        detection_language = ["ch_sim", "en"]
        self.reader = easyocr.Reader(detection_language)  # this needs to run only once to load the model into memory

    def __call__(self, image_path):
        if self.model is None:
            self._init()
        result = self.reader.readtext(image_path)
        return result
