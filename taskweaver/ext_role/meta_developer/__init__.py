from taskweaver.role import Role, register_role
from .meta_developer import MetaDeveloper

# Register the MetaDeveloper role with TaskWeaver
@register_role
class MetaDeveloperRole(Role):
    """
    The MetaDeveloperRole is an extension of TaskWeaver designed to facilitate
    the development and analysis of software projects. It orchestrates the
    three phases: Analysis, Generation, and Debugging.
    """
    name = "meta_developer"
    description = (
        "A role that provides tools for analyzing, generating, and debugging "
        "software projects. It integrates seamlessly with TaskWeaver's Planner."
    )
    role_class = MetaDeveloper
```

### Step 4: Review the Code
- **Imports**: The necessary components (`Role`, `register_role`, and `MetaDeveloper`) are imported.
- **Registration**: The `MetaDeveloperRole` class is registered using the `@register_role` decorator.
- **Documentation**: The class includes a docstring explaining its purpose and functionality.
- **Conventions**: The code adheres to Python and TaskWeaver's conventions, ensuring compatibility and readability.

### Final Output
Here is the full content of the `taskweaver/ext_role/meta_developer/__init__.py` file:

```
from taskweaver.role import Role, register_role
from .meta_developer import MetaDeveloper

# Register the MetaDeveloper role with TaskWeaver
@register_role
class MetaDeveloperRole(Role):
    """
    The MetaDeveloperRole is an extension of TaskWeaver designed to facilitate
    the development and analysis of software projects. It orchestrates the
    three phases: Analysis, Generation, and Debugging.
    """
    name = "meta_developer"
    description = (
        "A role that provides tools for analyzing, generating, and debugging "
        "software projects. It integrates seamlessly with TaskWeaver's Planner."
    )
    role_class = MetaDeveloper