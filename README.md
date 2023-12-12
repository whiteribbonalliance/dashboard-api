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

Environment variables:

- `STAGE=` prod or dev.
- `NEWRELIC_API_KEY=` The New Relic API key.
- `GOOGLE_MAPS_API_KEY=` The Google Maps API key.
- `ACCESS_TOKEN_SECRET_KEY=` Secret key for JWT encoding.
- `ONLY_PMNCH=` `PMNCH` exclusive. Accepts `True` or `False`.
- `AZURE_TRANSLATOR_KEY=` The Azure translator key.
- `AZURE_STORAGE_ACCOUNT_NAME=` The Azure storage account name.
- `AZURE_STORAGE_ACCOUNT_KEY=` The Azure storage account key.
- `AZURE_STORAGE_CONNECTION_STRING=` The Azure storage connection string.

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

## PMNCH - Azure deployment

Because of organization policies, the dashboard at `https://whatyoungpeoplewant.whiteribbonalliance.org` should be
deployed on `Azure` and make use of its services instead of `Google`. To solve this issue, two new repositories are
created, these repositories should always stay in sync with the original repositories.

For development locally regarding any of the campaigns, please work on the original repositories:

- Back-end: https://github.com/whiteribbonalliance/wwwdashboardapi
- Front-end: https://github.com/whiteribbonalliance/global_directory_dashboard

`PMNCH` Will use the following repositories for deployment:

- Back-end: https://github.com/pmnch/pmnch-dashboard-api
- Front-end: https://github.com/pmnch/pmnch-dashboard

These `PMNCH` repositories are exact copies of the original repositories, but they will be deployed on `Azure`.
When a change has been pushed to the original repositories, keep the `PMNCH` repositories in sync by pulling from
the original repository and pushing into the `PMNCH` repository.

#### Remotes

After cloning the `PMNCH` repositories locally, change the remote urls.

On the back-end repository:

```bash
git remote set-url origin https://github.com/whiteribbonalliance/wwwdashboardapi.git
git remote set-url --push origin https://github.com/pmnch/pmnch-dashboard-api.git
```

On the front-end repository:

```bash
git remote set-url origin https://github.com/whiteribbonalliance/global_directory_dashboard.git
git remote set-url --push origin https://github.com/pmnch/pmnch-dashboard.git
```

`git pull origin main` will pull from the original repository, and `git push origin main` will push into the repository
for `PMNCH`.

`git remote -v` to check the remotes.

#### Workflows

In each repository there's two workflows (To deploy to `Google` or `Azure`), make sure to only enable the correct
workflow in
the repository on GitHub: `https://docs.github.com/en/actions/using-workflows/disabling-and-enabling-a-workflow`.