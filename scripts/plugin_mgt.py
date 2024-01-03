import argparse
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from injector import Injector

from taskweaver.code_interpreter.code_generator.plugin_selection import PluginSelector
from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.logging import LoggingModule
from taskweaver.memory.plugin import PluginModule

parser = argparse.ArgumentParser()
parser.add_argument(
    "--project_dir",
    type=str,
    default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "project",
    ),
)
parser.add_argument("--refresh", action="store_true")
parser.add_argument("--show", action="store_true")

args = parser.parse_args()


class PluginManager:
    def __init__(self):
        app_injector = Injector([LoggingModule, PluginModule])
        app_config = AppConfigSource(
            config_file_path=os.path.join(
                args.project_dir,
                "taskweaver_config.json",
            ),
            app_base_path=args.project_dir,
        )
        app_injector.binder.bind(AppConfigSource, to=app_config)
        self.experience_generator = app_injector.create_object(PluginSelector)

    def refresh(self):
        self.experience_generator.refresh()
        print("Plugin embeddings refreshed.")

    def show(self):
        plugin_list = self.experience_generator.available_plugins
        for p in plugin_list:
            print(f"* Plugin Name: {p.name}")
            print(f"* Plugin Description: {p.spec.description}")
            print(f"* Plugin Embedding dim: {len(p.meta_data.embedding)}")
            print(f"* Plugin Embedding model: {p.meta_data.embedding_model}")
            print(f"* Plugin Args: {p.spec.args}")
            print(f"* Plugin Returns: {p.spec.returns}")
            print(f"_________________________________")


if __name__ == "__main__":
    plugin_manager = PluginManager()
    if args.refresh:
        plugin_manager.refresh()
    if args.show:
        plugin_manager.show()
