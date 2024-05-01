from taskweaver.plugin import Plugin, register_plugin

try:
    import soundfile as sf
    import torch
    from datasets import load_dataset
    from transformers import SpeechT5ForTextToSpeech, SpeechT5HifiGan, SpeechT5Processor
except ImportError:
    raise ImportError("Please install necessary packages before running the plugin")


class Text2SpeechModelInference:
    def __init__(self) -> None:
        self.processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
        self.model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
        self.vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")
        # load xvector containing speaker's voice characteristics from a dataset
        self.embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
        self.speaker_embeddings = torch.tensor(self.embeddings_dataset[7306]["xvector"]).unsqueeze(0)

    def predict(self, input: str) -> None:
        with torch.no_grad():
            inputs = self.processor(text=input, return_tensors="pt")
            speech = self.model.generate_speech(inputs["input_ids"], self.speaker_embeddings, vocoder=self.vocoder)
        file_path = "./speech.wav"
        sf.write(file_path, speech.numpy(), samplerate=16000)
        return file_path


@register_plugin
class Text2Speech(Plugin):
    model: Text2SpeechModelInference = None

    def _init(self) -> None:
        self.model = Text2SpeechModelInference()

    def __call__(self, input: str):
        if self.model is None:
            self._init()

        filepath = self.model.predict(input)
        return filepath
