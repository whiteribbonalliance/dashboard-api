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
python main.py
```

## Translations

### Back-end

To apply translations on the back-end data run:

```bash
python translate.py
```

Texts that have not been translated yet will be translated and saved to `translations.json`.

### Front-end

Copy and paste on a new line each text that needs to be translated to  `front_translations/to_translate.txt`.

To apply translations run:

```bash
python translate_front.py
```

Once translations have been applied, a new folder called `languages` should have been inside `front_translations`.

Copy the `translations` folder to the front-end project at `src/app/i18n`.

