# What Women Want Dashboard API

## What does this API do?

This API is used for retrieving campaign responses from BigQuery to display in a dashboard.

## Where is the URL?

https://www-dashboard-api-dot-deft-stratum-290216.uc.r.appspot.com/docs

## Continuous integration

This API is built automatically by GitHub actions.

The Docker container is pushed to Google Container Registry.

Then it is deployed to Google App Engine using a Flex environment (see `app.yaml`).

## Development

### install

Set the value for the environment variable `STAGE` as `dev`.

```bash
pip install -r requirements.txt
```

### Run

```bash
python run.py
```