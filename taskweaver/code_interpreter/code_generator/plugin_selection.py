from hashlib import md5
from typing import Dict, List

import numpy as np
from injector import inject
from sklearn.metrics.pairwise import cosine_similarity

from taskweaver.llm import LLMApi
from taskweaver.memory.plugin import PluginEntry, PluginRegistry
from taskweaver.utils import write_yaml


class SelectedPluginPool:
    def __init__(self):
        self.selected_plugin_pool = []
        self._previous_used_plugin_cache = []  # cache the plugins used in the previous code generation

    def add_selected_plugins(self, external_plugin_pool: List[PluginEntry]):
        """
        Add selected plugins to the pool
        """
        self.selected_plugin_pool = self.merge_plugin_pool(self.selected_plugin_pool, external_plugin_pool)

    def __len__(self) -> int:
        return len(self.selected_plugin_pool)

    def filter_unused_plugins(self, code: str):
        """
        Filter out plugins that are not used in the code generated by LLM
        """
        plugins_used_in_code = [p for p in self.selected_plugin_pool if p.name in code]
        self._previous_used_plugin_cache = self.merge_plugin_pool(
            self._previous_used_plugin_cache,
            plugins_used_in_code,
        )
        self.selected_plugin_pool = self._previous_used_plugin_cache

    def get_plugins(self) -> List[PluginEntry]:
        return self.selected_plugin_pool

    @staticmethod
    def merge_plugin_pool(pool1: List[PluginEntry], pool2: List[PluginEntry]) -> List[PluginEntry]:
        """
        Merge two plugin pools and remove duplicates
        """
        merged_list = pool1 + pool2
        result = []

        for item in merged_list:
            is_duplicate = False
            for existing_item in result:
                if item.name == existing_item.name:
                    is_duplicate = True
                    break
            if not is_duplicate:
                result.append(item)
        return result


class PluginSelector:
    @inject
    def __init__(
        self,
        plugin_registry: PluginRegistry,
        llm_api: LLMApi,
        plugin_only: bool = False,
    ):
        if plugin_only:
            self.available_plugins = [p for p in plugin_registry.get_list() if p.plugin_only is True]
        else:
            self.available_plugins = plugin_registry.get_list()
        self.llm_api = llm_api
        self.plugin_embedding_dict: Dict[str, List[float]] = {}

        self.refresh_message = (
            "Please cd to the `script` directory and "
            "run `python -m plugin_mgt --refresh` to refresh the plugin embedding."
        )

    def refresh(self):
        plugin_to_embedded = []
        for idx, p in enumerate(self.available_plugins):
            if (
                len(p.meta_data.embedding) > 0
                and p.meta_data.embedding_model == self.llm_api.embedding_service.config.embedding_model
                and p.meta_data.md5hash == md5((p.spec.name + p.spec.description).encode()).hexdigest()
            ):
                continue
            else:
                plugin_to_embedded.append((idx, p.name + ": " + p.spec.description))

        plugin_embeddings = self.llm_api.get_embedding_list([text for idx, text in plugin_to_embedded])

        for i, embedding in enumerate(plugin_embeddings):
            p = self.available_plugins[plugin_to_embedded[i][0]]
            p.meta_data.embedding = embedding
            p.meta_data.embedding_model = self.llm_api.embedding_service.config.embedding_model
            p.meta_data.md5hash = md5((p.spec.name + p.spec.description).encode()).hexdigest()
            write_yaml(p.meta_data.path, p.meta_data.to_dict())

    def load_plugin_embeddings(self):
        for idx, p in enumerate(self.available_plugins):
            # check if the plugin has embedding
            assert len(p.meta_data.embedding) > 0, f"Plugin {p.name} has no embedding. " + self.refresh_message
            # check if the plugin is using the same embedding model as the current session
            assert p.meta_data.embedding_model == self.llm_api.embedding_service.config.embedding_model, (
                f"Plugin {p.name} is using embedding model {p.meta_data.embedding_model}, "
                f"which is different from the one used by current session"
                f" ({self.llm_api.embedding_service.config.embedding_model}). "
                f"Please use the same embedding model or refresh the plugin embedding." + self.refresh_message
            )
            # check if the plugin has been modified
            assert p.meta_data.md5hash == md5((p.spec.name + p.spec.description).encode()).hexdigest(), (
                f"Plugin {p.name} has been modified. " + self.refresh_message
            )
            self.plugin_embedding_dict[p.name] = p.meta_data.embedding

    def plugin_select(self, user_query: str, top_k: int = 5) -> List[PluginEntry]:
        user_query_embedding = np.array(self.llm_api.get_embedding(user_query))

        similarities = []

        if top_k >= len(self.available_plugins):
            return self.available_plugins

        for p in self.available_plugins:
            similarity = cosine_similarity(
                user_query_embedding.reshape(
                    1,
                    -1,
                ),
                np.array(self.plugin_embedding_dict[p.name]).reshape(1, -1),
            )
            similarities.append((p, similarity))

        plugins_rank = sorted(
            similarities,
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]

        selected_plugins = [p for p, sim in plugins_rank]

        return selected_plugins
