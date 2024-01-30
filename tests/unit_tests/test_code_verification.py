from injector import Injector

from taskweaver.code_interpreter.code_verification import code_snippet_verification
from taskweaver.logging import LoggingModule

app_injector = Injector(
    [LoggingModule],
)


def test_import_allowed():
    allowed_modules = ["pandas", "matplotlib"]
    code_snippet = (
        "import numpy as np\n"
        "import matplotlib.pyplot as plt\n"
        "random_numbers = np.random.normal(size=100)\n"
        "plt.hist(random_numbers, bins=10, alpha=0.5)\n"
        "plt.title('Distribution of Random Numbers')\n"
        "plt.xlabel('Value')\n"
        "plt.ylabel('Frequency')\n"
        "# Displaying the plot\n"
        "plt.show()\n"
    )
    code_verify_errors = code_snippet_verification(
        code_snippet,
        allowed_modules=allowed_modules,
        code_verification_on=True,
        blocked_functions=[],
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 1


def test_block_function():
    blocked_functions = ["exec", "eval"]
    code_snippet = "exec('import os')\n" "eval('import sys')\n" "import os\n"
    code_verify_errors = code_snippet_verification(
        code_snippet,
        allowed_modules=["pandas", "os"],
        code_verification_on=True,
        blocked_functions=blocked_functions,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 2


def test_normal_code():
    allowed_modules = []
    code_snippet = (
        "with open('file.txt', 'r') as file:\n"
        "    content = file.read()\n"
        "    print(content)\n"
        "def greet(name):\n"
        "    return f'Hello, {name}!'\n"
        "name = 'John'\n"
        "print(greet(name))\n"
    )
    code_verify_errors = code_snippet_verification(
        code_snippet,
        allowed_modules=allowed_modules,
        code_verification_on=True,
        blocked_functions=[],
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 0
