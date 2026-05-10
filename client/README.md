### Setup / install

```bash
cd client
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Configure and run

The HabitHub API server must be running first.

```bash
python web_client.py

```
Optional flags:

```bash
python web_client.py --api-url [api-url] --api-key [api-key]
```

This launches a lightweight Flask server that:
- serves all client HTML from static files in `client/static`
- performs all page updates in browser JavaScript
- proxies `/api/*` requests to the API server to avoid Same Origin Policy issues

