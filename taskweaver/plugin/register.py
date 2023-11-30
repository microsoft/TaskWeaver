from typing import Any, Callable, Dict, List, Optional, Type, Union

from .base import Plugin

__all__: List[str] = [
    "register_plugin",
    "test_plugin",
]

register_plugin_inner: Optional[Callable[[Type[Plugin]], None]] = None


def register_plugin(func: Union[Callable[..., Any], Type[Plugin]]):
    """
    register a plugin, the plugin could be a class or a callable function

    :param func: the plugin class or a callable function
    """
    global register_plugin_inner

    if "register_plugin_inner" not in globals() or register_plugin_inner is None:
        print("no registry for loading plugin")
    elif isinstance(func, type) and issubclass(func, Plugin):
        register_plugin_inner(func)
    elif callable(func):
        func_name = func.__name__

        def callable_func(self: Plugin, *args: List[Any], **kwargs: Dict[str, Any]):
            self.log("info", "calling function " + func_name)
            result = func(*args, **kwargs)
            return result

        wrapper_cls = type(
            f"FuncPlugin_{func_name}",
            (Plugin,),
            {
                "__call__": callable_func,
            },
        )
        register_plugin_inner(wrapper_cls)
    else:
        raise Exception(
            "only callable function or plugin class could be registered as Plugin",
        )
    return func


register_plugin_test_inner: Optional[Callable[[str, str, Callable[..., Any]], None]] = None


def test_plugin(name: Optional[str] = None, description: Optional[str] = None):
    """
    register a plugin test
    """

    def inner(func: Callable[..., Any]):
        global register_plugin_test_inner

        if "register_plugin_test_inner" not in globals() or register_plugin_test_inner is None:
            print("no registry for loading plugin")

        elif callable(func):
            test_name: str = func.__name__ if name is None else name
            test_description: str = func.__doc__ or "" if description is None else description
            register_plugin_test_inner(test_name, test_description, func)

        return func

    return inner
