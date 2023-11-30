import os

from injector import Injector

from taskweaver.code_interpreter.code_generator import CodeVerificationConfig, code_snippet_verification
from taskweaver.config.config_mgt import AppConfigSource
from taskweaver.logging import LoggingModule

app_injector = Injector(
    [LoggingModule],
)

app_config = AppConfigSource(
    config={
        "app_dir": os.path.dirname(os.path.abspath(__file__)),
        "code_verification.code_verification_on": True,
        "code_verification.allowed_modules": [
            "pandas",
            "matplotlib",
            "numpy",
            "sklearn",
            "scipy",
            "seaborn",
            "datetime",
            "os",
        ],
        "code_verification.plugin_only": True,
    },
)
app_injector.binder.bind(AppConfigSource, to=app_config)

code_verification_config = app_injector.create_object(CodeVerificationConfig)


def test_plugin_only():
    code_verification_config.plugin_only = True
    code_snippet = (
        "anomaly_detection()\n"
        "s = timext()\n"
        "result, var = anomaly_detection()\n"
        "result, var\n"
        "result\n"
        "var\n"
        "s\n"
    )
    code_verify_errors = code_snippet_verification(
        code_snippet,
        ["anomaly_detection"],
        code_verification_config,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 2


def test_import_allowed():
    code_verification_config.plugin_only = False
    code_verification_config.allowed_modules = ["pandas", "matplotlib"]
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
        ["anomaly_detection"],
        code_verification_config,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 1


def test_normal_code():
    code_verification_config.plugin_only = False
    code_verification_config.allowed_modules = []
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
        ["anomaly_detection"],
        code_verification_config,
    )
    print("---->", code_verify_errors)
    assert len(code_verify_errors) == 0
