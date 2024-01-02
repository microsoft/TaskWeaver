import argparse
import os

from injector import Injector

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.logging import LoggingModule
from taskweaver.memory.experience import ExperienceGenerator

parser = argparse.ArgumentParser()
parser.add_argument("--refresh", action="store_true")
parser.add_argument(
    "--delete",
    metavar="EXP_ID",
    type=str,
    help="Delete experience with experience id, e.g., exp_{ID}.yaml",
)
parser.add_argument("--show", action="store_true")

args = parser.parse_args()


class ExperienceManager:
    def __init__(self):
        app_injector = Injector([LoggingModule])
        app_config = AppConfigSource(
            config_file_path=os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..",
                "project/taskweaver_config.json",
            ),
            app_base_path=os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..",
                "project",
            ),
        )
        app_injector.binder.bind(AppConfigSource, to=app_config)
        self.experience_generator = app_injector.create_object(ExperienceGenerator)
        self.experience_generator.summarize_experience_in_batch(refresh=False)

    def refresh(self):
        self.experience_generator.summarize_experience_in_batch(refresh=True)
        print("Refreshed experience list")

    def delete(self, session_id: str):
        self.experience_generator.delete_experience(session_id=session_id)
        self.experience_generator.delete_raw_experience(session_id=session_id)
        print(f"Deleted experience with id: {session_id}")

    def show(self):
        for exp in self.experience_generator.experience_list:
            print(f"* Experience ID: {exp.session_id}")
            print(f"* Experience Text: {exp.experience_text}")
            print(f"* Experience Embedding Dim: {len(exp.embedding)}")
            print(f"* Experience Embedding Model: {exp.embedding_model}")
            print(f"* Experience Raw Path: {exp.raw_experience_path}")
            print("_________________________")


if __name__ == "__main__":
    experience_manager = ExperienceManager()
    if args.refresh:
        experience_manager.refresh()
    if args.delete:
        experience_manager.delete(args.delete)
    if args.show:
        experience_manager.show()
