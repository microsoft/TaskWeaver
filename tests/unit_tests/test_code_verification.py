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


def test_dynamic_attribute_access_getattr():
    """Test that getattr() is blocked as it can bypass security checks."""
    blocked_functions = ["getattr"]
    code_snippet = "obj = object()\n" "method = getattr(obj, 'some_method')\n"
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
        blocked_functions=blocked_functions,
    )
    print("---->", code_verify_errors)
    # Should detect getattr as blocked function + dangerous builtin
    assert len(code_verify_errors) >= 1
    assert any("getattr" in err for err in code_verify_errors)


def test_dynamic_attribute_access_setattr():
    """Test that setattr() is blocked as it can bypass security checks."""
    blocked_functions = ["setattr"]
    code_snippet = "obj = object()\n" "setattr(obj, 'dangerous_attr', 'value')\n"
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
        blocked_functions=blocked_functions,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) >= 1
    assert any("setattr" in err for err in code_verify_errors)


def test_dangerous_builtins_globals_locals():
    """Test that globals() and locals() are blocked."""
    blocked_functions = ["globals", "locals"]
    code_snippet = "g = globals()\n" "l = locals()\n"
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
        blocked_functions=blocked_functions,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) >= 2
    assert any("globals" in err for err in code_verify_errors)
    assert any("locals" in err for err in code_verify_errors)


def test_dunder_attribute_access():
    """Test that direct access to dangerous dunder attributes is blocked."""
    code_snippet = "obj = object()\n" "cls = obj.__class__\n" "bases = cls.__bases__\n"
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
    )
    print("---->", code_verify_errors)
    # Should detect __class__ and __bases__ as dangerous attributes
    assert len(code_verify_errors) >= 2
    assert any("__class__" in err for err in code_verify_errors)
    assert any("__bases__" in err for err in code_verify_errors)


def test_subscript_based_dunder_access():
    """Test that subscript-based access to dunder attributes is blocked."""
    code_snippet = "obj = {}\n" "dangerous = obj['__class__']\n"
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) >= 1
    assert any("__class__" in err for err in code_verify_errors)


def test_subscript_function_call_bypass():
    """Test that subscript-based function calls are blocked."""
    code_snippet = "methods = {'dangerous': eval}\n" "result = methods['dangerous']('print(1)')\n"
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
    )
    print("---->", code_verify_errors)
    # Should detect subscript-based function call pattern
    assert len(code_verify_errors) >= 1


def test_dict_access_to_builtins():
    """Test that accessing __builtins__ via __dict__ is blocked."""
    code_snippet = "import sys\n" "builtins = sys.modules['__builtins__']\n"
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) >= 1
    assert any("__builtins__" in err for err in code_verify_errors)


def test_vars_function_blocked():
    """Test that vars() function is blocked as it exposes object internals."""
    blocked_functions = ["vars"]
    code_snippet = "obj = object()\n" "attributes = vars(obj)\n"
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
        blocked_functions=blocked_functions,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) >= 1
    assert any("vars" in err for err in code_verify_errors)


def test_delattr_blocked():
    """Test that delattr() is blocked."""
    blocked_functions = ["delattr"]
    code_snippet = "class Foo:\n    x = 1\n" "delattr(Foo, 'x')\n"
    code_verify_errors = code_snippet_verification(
        code_snippet,
        code_verification_on=True,
        blocked_functions=blocked_functions,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) >= 1
    assert any("delattr" in err for err in code_verify_errors)
