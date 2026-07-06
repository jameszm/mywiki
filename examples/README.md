# Examples

Test repositories used as input for the wiki generator.

## requests

- Source: https://github.com/psf/requests
- Why chosen:
  - Small enough to iterate cheaply (~19 Python files in `src/requests/`)
  - Real multi-component architecture: `Session` (sessions.py), transport adapters (adapters.py), request/response models (models.py), auth, cookies, hooks — good material for an interactive architecture graph
  - Massive online footprint: thousands of GitHub issues, blog posts, Stack Overflow content — ideal for testing the external-enrichment layer
  - Permissive license (Apache 2.0)

Cloned repositories are gitignored. To re-fetch:

```bash
git clone --depth 1 https://github.com/psf/requests examples/requests
```
