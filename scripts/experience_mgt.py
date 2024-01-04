import argparse
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from injector import Injector

from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.logging import LoggingModule
from taskweaver.memory.experience import ExperienceGenerator

parser = argparse.ArgumentParser()
parser.add_argument("--target_role", type=str, choices=["Planner", "CodeInterpreter"], required=True)
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
parser.add_argument(
    "--delete",
    metavar="EXP_ID",
    type=str,
    help="Delete experience with experience id, e.g., exp_{ID}.yaml",
)
parser.add_argument("--delete_raw", metavar="EXP_ID", type=str, help="Delete raw experience with experience id")
parser.add_argument(
    "--delete_handcraft",
    metavar="EXP_ID",
    type=str,
    help="Delete handcraft experience with experience id",
)
parser.add_argument("--show", action="store_true")

args = parser.parse_args()


class ExperienceManager:
    def __init__(self):
        app_injector = Injector([LoggingModule])
        app_config = AppConfigSource(
            config_file_path=os.path.join(
                args.project_dir,
                "taskweaver_config.json",
            ),
            app_base_path=args.project_dir,
        )
        app_injector.binder.bind(AppConfigSource, to=app_config)
        self.experience_generator = app_injector.create_object(ExperienceGenerator)

    def refresh(self):
        self.experience_generator.refresh(args.target_role)
        print("Refreshed experience list")

    def delete_experience(self, exp_id: str):
        self.experience_generator.delete_experience(exp_id=exp_id, target_role=args.target_role)
        print(f"Deleted experience with id: {exp_id}")

    def delete_raw_experience(self, exp_id: str):
        self.experience_generator.delete_raw_experience(exp_id=exp_id)
        print(f"Deleted raw experience with id: {exp_id}")

    def delete_handcraft_experience(self, exp_id: str):
        self.experience_generator.delete_handcrafted_experience(exp_id=exp_id)
        print(f"Deleted handcraft experience with id: {exp_id}")

    def show(self):
        self.experience_generator.load_experience(args.target_role)
        if len(self.experience_generator.experience_list) == 0:
            print("No experience found")
            return
        for exp in self.experience_generator.experience_list:
            print(f"* Experience ID: {exp.exp_id}")
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
        experience_manager.delete_experience(args.delete)
    if args.delete_raw:
        experience_manager.delete_raw_experience(args.delete_raw)
    if args.delete_handcraft:
        experience_manager.delete_handcraft_experience(args.delete_handcraft)
    if args.show:
        experience_manager.show()
