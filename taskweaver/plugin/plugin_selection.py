from typing import List

from injector import inject

from taskweaver.memory.plugin import PluginEntry, PluginRegistry


class PluginSelector:
    @inject
    def __init__(self, plugin_registry: PluginRegistry):
        self.plugin_registry = plugin_registry
        self.embedding_generator = self.plugin_registry.embedding_generator
        self.selected_plugins_pool = []

    @staticmethod
    def merge_plugin_pool(pool1: List[PluginEntry], pool2: List[PluginEntry]):
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

    def plugin_select(self, user_query: str, top_k: int = 5) -> List[PluginEntry]:
        try:
            import numpy as np
        except ImportError:
            raise Exception(
                "Package numpy is required for using auto plugin selection. "
                "Please install it using pip install numpy",
            )

        try:
            from sklearn.metrics.pairwise import cosine_similarity
        except Exception:
            raise Exception(
                "Package scikit-learn is required for using auto plugin selection. "
                "Please install it using pip install scikit-learn",
            )

        user_query_embedding = np.array(self.embedding_generator.get_embedding(user_query))

        similarities = []

        assert (
            len(
                self.plugin_registry.get_list(),
            )
            >= top_k
        ), "the number of plugins to be selected should be larger than top_k"

        for p in self.plugin_registry.get_list():
            similarity = cosine_similarity(
                user_query_embedding.reshape(
                    1,
                    -1,
                ),
                np.array(p.spec.embedding).reshape(1, -1),
            )
            similarities.append((p, similarity))

        plugins_rank = sorted(
            similarities,
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]

        selected_plugins = [p for p, sim in plugins_rank]
        self.selected_plugins_pool = self.merge_plugin_pool(self.selected_plugins_pool, selected_plugins)

        return selected_plugins
