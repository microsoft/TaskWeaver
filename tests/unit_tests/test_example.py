import os

from taskweaver.misc.example import load_examples


def test_load_examples():
    example_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "examples",
        "planner_examples",
    )
    sub_path = ""
    examples = load_examples(example_path, sub_path, {"Planner", "User", "CodeInterpreter"})
    assert len(examples) == 1

    examples = load_examples(example_path, sub_path)
    assert len(examples) == 1

    examples = load_examples(example_path, sub_path, {"Planner"})
    assert len(examples) == 0

    examples = load_examples(example_path, sub_path, {"User"})
    assert len(examples) == 0

    examples = load_examples(example_path, sub_path, {"Planner", "User", "Other"})
    assert len(examples) == 0

    examples = load_examples(example_path, sub_path, {"Planner", "User", "CodeInterpreter", "Other"})
    assert len(examples) == 1


def test_load_sub_examples():
    example_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "examples",
        "planner_examples",
    )
    sub_path = "sub"
    examples = load_examples(example_path, sub_path, {"Planner", "User", "CodeInterpreter"})
    assert len(examples) == 1

    examples = load_examples(example_path, sub_path)
    assert len(examples) == 1

    examples = load_examples(example_path, sub_path, {"Planner"})
    assert len(examples) == 0

    examples = load_examples(example_path, sub_path, {"User"})
    assert len(examples) == 0

    examples = load_examples(example_path, sub_path, {"Planner", "User", "Other"})
    assert len(examples) == 0

    examples = load_examples(example_path, sub_path, {"Planner", "User", "CodeInterpreter", "Other"})
    assert len(examples) == 1
