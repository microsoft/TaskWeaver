from taskweaver.plugin import Plugin, register_plugin

try:
    import whisper
except ImportError:
    raise ImportError(
        "Please install whisper with `pip install -U openai-whisper`. "
        "If any error happens, please refer the readme: https://github.com/openai/whisper/tree/main?tab=readme-ov-file",
    )


@register_plugin
class Speech2Text(Plugin):
    model = None

    def _init(self) -> None:
        self.model = whisper.load_model("base")
        self.device = self.model.device

    def __call__(self, audio_path):
        if self.model is None:
            self._init()
        # load audio and pad/trim it to fit 30 seconds
        audio = whisper.load_audio(audio_path)
        audio = whisper.pad_or_trim(audio)

        mel = whisper.log_mel_spectrogram(audio).to(self.device)

        options = whisper.DecodingOptions()
        result = whisper.decode(self.model, mel, options)
        return result.text
