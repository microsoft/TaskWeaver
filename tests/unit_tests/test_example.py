import os

from taskweaver.misc.example import load_examples


def test_load_examples():
    example_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "examples",
        "planner_examples",
    )
    examples = load_examples(example_path, {"Planner", "User", "CodeInterpreter"})
    assert len(examples) == 1

    examples = load_examples(example_path)
    assert len(examples) == 1

    examples = load_examples(example_path, {"Planner"})
    assert len(examples) == 0

    examples = load_examples(example_path, {"User"})
    assert len(examples) == 0

    examples = load_examples(example_path, {"Planner", "User", "Other"})
    assert len(examples) == 0

    examples = load_examples(example_path, {"Planner", "User", "CodeInterpreter", "Other"})
    assert len(examples) == 1
