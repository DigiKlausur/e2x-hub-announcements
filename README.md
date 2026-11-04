# e2x-hub-announcements

[![PyPI](https://img.shields.io/pypi/v/e2x-hub-announcements?include_prereleases)](https://pypi.org/project/e2x-hub-announcements/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)

`e2x-hub-announcements` is a small announcement service for [JupyterHub](https://jupyterhub.readthedocs.io/) (z2jh) deployments. Admins write an announcement in a web UI and choose which hub pages it appears on, its severity, and when it expires. It shows up on the next page load, with no hub restart.

```text
 admin browser ──► /services/announcements/  (FastAPI service, managed by hub)
                         │ writes
                         ▼
            /srv/jupyterhub/announcements.json   (hub PVC)
                         ▲ reads on each page render
                         │
 any user ──► hub page ──┘  template_vars callables → announcement_<page>
```

The hub renders the banner itself through JupyterHub's stock `announcement_<page>` template variables. Banners need no JavaScript or polling, and spawner templates need no changes.

> **Status:** pre-release (`0.1.0rc0`). The features below work, but the interface may still change before `0.1.0`. Please report problems in the [issue tracker](https://github.com/Digiklausur/e2x-hub-announcements/issues).

---

## What does it provide?

* **Admin service** (`e2x_hub_announcements.service`): a FastAPI app with an admin UI and API. Admins create announcements with target pages (spawn, login, home, logout), a severity (`info`, `warning`, `alert`) and an expiry, preview them, and end them early.
* **Hub integration** (`e2x_hub_announcements.hub`): `configure_announcements(c, store_path=...)` registers `template_vars` callables that read the store on each page render and return the active banners for that page.
* **`page.html` override** (`share/e2x_hub_announcements/templates/jupyterhub/`): replaces only the stock `announcement` block, so banners render in their severity colour instead of the stock yellow warning box.

---

## Installation

Install the package into the hub image:

```bash
pip install e2x-hub-announcements
```

---

## JupyterHub integration

The same z2jh values work for any hub:

```yaml
hub:
  services:
    announcements:
      url: http://hub:<port>
      command: [uvicorn, e2x_hub_announcements.service:app]
      environment:
        UVICORN_HOST: "0.0.0.0"
        UVICORN_PORT: "<port>"
        ANNOUNCEMENTS_STORE: /srv/jupyterhub/announcements.json
  extraConfig:
    10-announcements.py: |
      from e2x_hub_announcements.hub import configure_announcements
      configure_announcements(c, store_path="/srv/jupyterhub/announcements.json")
```

Like other managed services, it also needs a `hub.service.extraPorts` entry and a `hub.networkPolicy.ingress` rule for `<port>`. Give `access:services!service=announcements` to admins only, not to the default `user` role.

### Severity styling and `template_paths`

The stock `page.html` wraps every announcement in a yellow `alert-warning` box. To show the severity colour instead, `configure_announcements` puts this package's `page.html` override **first** in `c.JupyterHub.template_paths`. Every hub page that extends `page.html` picks it up, including custom templates that extend `templates/spawn.html`.

* **Add to `template_paths`, don't assign it.** Other config that runs after `configure_announcements` must use `c.JupyterHub.template_paths.append(...)` (or `+=`). An assignment like `c.JupyterHub.template_paths = [...]` silently removes the override. Banners then still show, but always in the yellow box.
* **Only one `page.html` override can apply.** The override extends the stock `templates/page.html` directly, so it shadows any other `page.html` in `template_paths` (e.g. a theme).
* Templates that extend `templates/page.html` directly (with the prefix) bypass the override.

---

## API

All paths are relative to the service prefix (e.g. `/services/announcements`). Every endpoint requires `access:services!service=announcements`. Interactive docs are at `<prefix>/docs`.

| Method | Path                               | Purpose                                         |
| ------ | ---------------------------------- | ----------------------------------------------- |
| GET    | `/`                                | Admin UI: create, preview, end and delete announcements |
| GET    | `/api/announcements`               | List all announcements (active and expired), newest first |
| POST   | `/api/announcements`               | Create an announcement (`expires_at` must be in the future, with a timezone) |
| POST   | `/api/announcements/{id}/end`      | Expire an announcement now                      |
| DELETE | `/api/announcements/{id}`          | Remove an announcement                          |
| POST   | `/api/preview`                     | Render the banner HTML without saving           |

---

## Development

```bash
git clone https://github.com/Digiklausur/e2x-hub-announcements.git
cd e2x-hub-announcements
pip install -e ".[dev,test]"
pytest
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
