# Deployment

Live application: [Hong Kong FPS Trends Dashboard](https://hong-kong-fps-dashboard.streamlit.app/). Deployed on 17 September 2026 using Python 3.13.

The application runs as a Python service. GitHub hosts the source code; GitHub Pages does not run the Streamlit server.

## Streamlit Community Cloud

Use the following configuration:

| Setting | Value |
|---|---|
| Repository | `CardiFfung/hong-kong-fps-dashboard` |
| Branch | `main` |
| Entrypoint | `app.py` |
| Python version | `3.13` |
| Dependency file | `requirements.txt` |
| Secrets | None required for the public HKMA APIs |

Create an app in Streamlit Community Cloud, select the repository and entrypoint, and set the Python version in Advanced settings. The dashboard theme is defined in `.streamlit/config.toml`.

See the official [deployment instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) and [dependency documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

## Data Persistence

Commit `data/current.json` together with its corresponding raw and processed snapshot directories. The app reads the included snapshot on startup and contacts HKMA when a user requests an update.

Runtime updates write new snapshots to the host filesystem. These files may not survive a cloud restart. For durable updates, refresh the repository snapshot or configure persistent storage. No scheduled refresh is configured.

## Release Checks

1. Confirm the displayed data month and retrieval time.
2. Check the five charts and switch the date range, metric, and payment category.
3. Download a CSV and compare its period and totals with the selected data.
4. Run the test suite, including the simulated API-failure and missing-snapshot cases.
5. Verify that the live URL in the README still resolves to the deployed app.
