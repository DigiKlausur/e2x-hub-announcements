import os

from jinja2 import ChoiceLoader, DictLoader, Environment, FileSystemLoader, PrefixLoader

from e2x_hub_announcements._data import JUPYTERHUB_TEMPLATE_PATH

# Minimal stand-in for JupyterHub's stock page.html announcement block.
STOCK_PAGE = """\
<body>
{% block announcement %}
  {% if announcement %}
<div class="container text-center announcement alert alert-warning">{{ announcement | safe }}</div>
  {% endif %}
{% endblock announcement %}
</body>
"""


def hub_environment() -> Environment:
    """Mimic JupyterHub's loader: template_paths first, stock files also under 'templates/'."""
    return Environment(
        loader=ChoiceLoader(
            [
                FileSystemLoader([JUPYTERHUB_TEMPLATE_PATH]),
                PrefixLoader({"templates": DictLoader({"page.html": STOCK_PAGE})}),
            ]
        )
    )


def test_override_is_found():
    assert os.path.isfile(os.path.join(JUPYTERHUB_TEMPLATE_PATH, "page.html"))


def test_banner_is_rendered_without_stock_wrapper():
    banner = '<div class="alert alert-info">Hi</div>'
    html = hub_environment().get_template("page.html").render(announcement=banner)
    assert banner in html
    assert "alert-warning" not in html


def test_no_announcement_renders_nothing():
    html = hub_environment().get_template("page.html").render(announcement=None)
    assert "alert" not in html
