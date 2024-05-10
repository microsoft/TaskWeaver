from taskweaver.code_interpreter.code_verification import code_snippet_verification


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
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 1

    allowed_modules = []
    code_verify_errors = code_snippet_verification(
        code_snippet,
        allowed_modules=allowed_modules,
        code_verification_on=True,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 2

    allowed_modules = None
    code_verify_errors = code_snippet_verification(
        code_snippet,
        allowed_modules=allowed_modules,
        code_verification_on=True,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 0


def test_import_blocked():
    blocked_modules = ["numpy", "matplotlib"]
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
        blocked_modules=blocked_modules,
        code_verification_on=True,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 2

    blocked_modules = []
    code_verify_errors = code_snippet_verification(
        code_snippet,
        blocked_modules=blocked_modules,
        code_verification_on=True,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 0

    blocked_modules = None
    code_verify_errors = code_snippet_verification(
        code_snippet,
        blocked_modules=blocked_modules,
        code_verification_on=True,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 0


def test_import_allowed_and_blocked():
    try:
        allowed_modules = ["numpy", "matplotlib"]
        blocked_modules = ["numpy", "matplotlib"]
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
        code_snippet_verification(
            code_snippet,
            allowed_modules=allowed_modules,
            blocked_modules=blocked_modules,
            code_verification_on=True,
        )
        assert False, "Should raise an error"
    except AssertionError as e:
        print("---->", e)


def test_block_function():
    blocked_functions = ["exec", "eval"]
    code_snippet = "exec('import os')\n" "eval('import sys')\n" "print('Hello, World!')\n"
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
        blocked_functions=blocked_functions,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 2

    blocked_functions = []
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
        blocked_functions=blocked_functions,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 0

    blocked_functions = None
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
        blocked_functions=blocked_functions,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 0


def test_allow_function():
    allowed_functions = ["print", "abs"]
    code_snippet = "exec('import os')\n" "eval('import sys')\n" "print('Hello, World!')\n"
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
        allowed_functions=allowed_functions,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 2

    allowed_functions = []
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
        allowed_functions=allowed_functions,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 3

    allowed_functions = None
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
        allowed_functions=allowed_functions,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 0


def test_allow_block_function():
    try:
        allowed_functions = ["print", "abs"]
        blocked_functions = ["exec", "eval"]
        code_snippet = "exec('import os')\n" "eval('import sys')\n" "print('Hello, World!')\n"
        code_snippet_verification(
            code_snippet,
            code_verification_on=True,
            allowed_functions=allowed_functions,
            blocked_functions=blocked_functions,
        )
        assert False, "Should raise an error"
    except AssertionError as e:
        print("---->", e)


def test_allow_variable():
    allowed_variables = ["name", "age"]
    code_snippet = "name = 'John'\n" "age = 25\n" "print(f'Hello, {name}! You are {age} years old.')\n"
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
        allowed_variables=allowed_variables,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 0

    allowed_variables = []
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
        allowed_variables=allowed_variables,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 2

    allowed_variables = None
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
        allowed_variables=allowed_variables,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 0

    code_snippet = "name, age = 'John', 25\n" "print(f'Hello, {name}! You are {age} years old.')\n"
    allowed_variables = ["name", "age"]
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
        allowed_variables=allowed_variables,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 0


def test_magic_code():
    code_snippet = (
        "!pip install pandas\n"
        "import numpy as np\n"
        "import matplotlib.pyplot as plt\n"
        "random_numbers = np.random.normal(size=100)\n"
        "plt.hist(random_numbers, bins=10, alpha=0.5)\n"
        "plt.title('Distribution of Random Numbers')\n"
        "plt.xlabel('Value')\n"
        "plt.ylabel('Frequency')\n"
        "# Displaying the plot\n"
        "plt.show()\n"
        "%matplotlib inline\n"
        "import pandas as pd\n"
        "df = pd.DataFrame({'name': ['John', 'Alice', 'Bob'], 'age': [25, 30, 35]})\n"
        "df\n"
    )
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 1
    assert "Magic commands except package install are not allowed" in code_verify_errors[0]
