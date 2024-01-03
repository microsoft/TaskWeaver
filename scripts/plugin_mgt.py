import argparse
import os

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
        self.experience_generator.generate_plugin_embeddings(refresh=True)
        print("Plugin embeddings refreshed.")

    def show(self):
        plugin_list = self.experience_generator.available_plugins
        for p in plugin_list:
            print(f"* Plugin name: {p.name}")
            print(f"* Plugin description: {p.spec.description}")
            print(f"* Plugin embedding dim: {len(p.spec.embedding)}")
            print(f"* Plugin embedding model: {p.spec.embedding_model}")
            print(f"* Plugin args: {p.spec.args}")
            print(f"* Plugin returns: {p.spec.returns}")
            print(f"_________________________________")


if __name__ == "__main__":
    plugin_manager = PluginManager()
    if args.refresh:
        plugin_manager.refresh()
    if args.show:
        plugin_manager.show()
