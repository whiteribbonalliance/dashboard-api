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

Translations occur automatically on the fly.

### Front-end

Create a JSON file at `front_translations/to_translate.json` that contains the keys that will be used in the front for
accessing translations and use as value the text in English.

For example:

```json
{
  "title": "Lorem Ipsum",
  "click-button": "Click button"
}
```

To apply translations run:

```bash
python scripts/translate_front.py
```

Once translations have been applied, a new folder called `languages` should have been created
inside `front_translations`.

Copy the `translations` folder to the front-end project at `src/app/i18n`.

*Note: Only texts that have not been translated yet will be translated and saved to `translations.json`.*

## How to add a new campaign

1. Add campaign code to `app/enums/campaign_code.py`.
2. Create new database for campaign at `app/databases.py` and add the new database to `databases` dictionary.
3. In `app/services/campaign.py` modify any of the functions if needed for the campaign.
4. In `app/databases.py` include the new `q_cdoe` for the campaign.