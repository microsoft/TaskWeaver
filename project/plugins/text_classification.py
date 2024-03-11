from typing import List

from taskweaver.plugin import Plugin, register_plugin

try:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
except ImportError:
    raise ImportError("Please install transformers with `pip install transformers`.")
try:
    import torch
except ImportError:
    raise ImportError(
        "Please install torch according to your OS and CUDA availability. You may try `pip install torch`",
    )


class TextClassificationModelInference:
    """This text classification model inference class is for zero-shot text classification using
    Huggingface's transformers library. The method works by posing the sequence to be classified
    as the NLI premise and to construct a hypothesis from each candidate label.
    More details can be found at: https://huggingface.co/facebook/bart-large-mnli
    """

    def __init__(self, model_name: str) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(self.device)

        self.entailment_id = -1
        for idx, label in self.model.config.id2label.items():
            if label.lower().startswith("entail"):
                self.entailment_id = int(idx)
        if self.entailment_id == -1:
            raise ValueError("Could not determine the entailment ID from the model config, please pass it at init.")

    def predict(self, inputs: List[str], label_list: List[str]) -> List[str]:
        predicted_labels = []
        for sequence in inputs:
            tokenized_inputs = self.tokenizer(
                [sequence] * len(label_list),
                [f"This example is {label}" for label in label_list],
                return_tensors="pt",
                padding="max_length",
            )
            with torch.no_grad():
                logits = self.model(**tokenized_inputs.to(self.device)).logits
                label_id = torch.argmax(logits[:, 2]).item()
                predicted_labels.append(label_list[label_id])
        return predicted_labels


@register_plugin
class TextClassification(Plugin):
    model: TextClassificationModelInference = None

    def _init(self) -> None:
        model_name = "facebook/bart-large-mnli"
        self.model = TextClassificationModelInference(model_name)

    def __call__(self, inputs: List[str], label_list: List[str]) -> List[str]:
        if self.model is None:
            self._init()

        result = self.model.predict(inputs, label_list)
        return result
