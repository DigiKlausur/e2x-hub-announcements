# e2x-hub-announcements

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)

`e2x-hub-announcements` is a small announcement service for [JupyterHub](https://jupyterhub.readthedocs.io/) (z2jh) deployments. Admins write an announcement in a web UI and choose which hub pages it appears on, its severity, and when it expires. It shows up on the next page load, with no hub restart.

It has no dependency on `e2x-course-hub`, so it can run on any hub.

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

See [announcements.md](announcements.md) for the full design.

> **Status:** early development (`0.1.0-rc0`). The sections below describe the planned interface.

---

## What does it provide?

* **Admin service** (`e2x_hub_announcements.service`): a FastAPI app with an admin UI and API. Admins create announcements with target pages (spawn, login, home, logout), a severity (`info`, `warning`, `alert`) and an expiry, preview them, and end them early.
* **Hub integration** (`e2x_hub_announcements.hub`): `configure_announcements(c, store_path=...)` registers `template_vars` callables that read the store on each page render and return the active banners for that page.

---

## Installation

This package is not yet published. Install it from source into the hub image:

```bash
git clone https://github.com/Digiklausur/e2x-hub-announcements.git
cd e2x-hub-announcements
pip install -e .
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
