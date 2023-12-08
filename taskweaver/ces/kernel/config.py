from cycler import cycler
from traitlets.config import get_config

c = get_config()

# IPKernelApp configuration
# c.IPKernelApp.name = "taskweaver"

# InteractiveShellApp configuration
c.InteractiveShellApp.extensions = ["taskweaver.ces.kernel.ctx_magic"]
c.InteractiveShell.ast_node_interactivity = "last_expr_or_assign"
c.InteractiveShell.banner1 = "Welcome to Task Weaver!"
c.InteractiveShell.color_info = False
c.InteractiveShell.colors = "NoColor"

# inline backend configuration
c.InlineBackend.figure_formats = ["png"]
c.InlineBackend.rc = {
    "text.color": (0.25, 0.25, 0.25),
    "axes.titlesize": 14,
    "axes.labelsize": 11,
    "axes.edgecolor": (0.15, 0.15, 0.2),
    "axes.labelcolor": (0.15, 0.15, 0.2),
    "axes.linewidth": 1,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.bottom": True,
    "axes.spines.left": True,
    "axes.grid": True,
    "grid.alpha": 0.75,
    "grid.linestyle": "--",
    "grid.linewidth": 0.6,
    "axes.prop_cycle": cycler("color", ["#10A37F", "#147960", "#024736"]),
    "lines.linewidth": 1.5,
    "lines.markeredgewidth": 0.0,
    "scatter.marker": "x",
    "xtick.labelsize": 12,
    "xtick.color": (0.1, 0.1, 0.1),
    "xtick.direction": "in",
    "ytick.labelsize": 12,
    "ytick.color": (0.1, 0.1, 0.1),
    "ytick.direction": "in",
    "figure.figsize": (12, 6),
    "figure.dpi": 200,
    "savefig.dpi": 200,
}
