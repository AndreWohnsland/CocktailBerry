# CocktailBerry Microservice

This is the subdirectory for the CocktailBerry microservice.
It contains the code for the according optional microservice to move some (not core) tasks from the main app.
It is also used to decouple external calls (e.g. to Webhooks or the dashboard) from the main app.
The microservice is written in Python and uses FastAPI as the web framework.

## Getting Started

Use uv to run the microservice locally:

```bash
uv run app.py
```
