# Dashboard API

## What does this API do?

This API is used for providing campaign data to display in the front-end dashboard. Follow the steps at
section `How to create a new campaign`. Once a new campaign configuration was added, the data will become available
through the endpoints. For more information, continue reading the documentation below.

There's currently six dashboards deployed with this project, you can visit them at:

- https://explore.whiteribbonalliance.org/en/whatwomenwant
- https://explore.whiteribbonalliance.org/en/midwivesvoices
- https://explore.whiteribbonalliance.org/en/wwwpakistan
- https://explore.whiteribbonalliance.org/en/healthwellbeing
- https://explore.whiteribbonalliance.org/en/giz
- https://wypw.1point8b.org/en

The configurations for these dashboards are included in `campaigns-configurations`, by running this API you can view
their respective dashboards by running the front-end.

## Environment variables:

### Required:

- `STAGE=` prod or dev.
- `ALLOW_ORIGINS=` Allow origins e.g. "https://example1.com https://example2.com"

### Optional:

- `ACCESS_TOKEN_SECRET_KEY=` Secret key for JWT encoding - Used for all protected paths
  e.g. `/api/v1/campaigns/{campaign_code}/data/`.
- `NEWRELIC_API_KEY=` The New Relic API key.
- `NEW_RELIC_URL=` The New Relic URL.
- `TRANSLATIONS_ENABLED=` True or False.
- `CLOUD_SERVICE=` `google` or `azure`. The cloud service will be used for translations if enabled, loading
  CSV files if you choose to do so from the cloud, and caching CSV files for downloading. Must be set if using any of
  the functionalities mentioned.
- `GOOGLE_MAPS_API_KEY=` Google Maps API key used only for campaigns `wwwpakistan` and `giz` if new regions
  are found (when new data is added to these campaigns).
- `INCLUDE_ALLCAMPAIGNS=` True or False. Allow displaying dashboard of all data merged together at `/allcampaigns`.
- `RELOAD_DATA_EVERY_12TH_HOUR=` True or False. Allows reloading CSV file from source every 12th hour.
- `{CAMPAIGN_CODE}_PASSWORD=` A password for accessing protected paths of a campaign
  e.g. `my_campaign_PASSWORD=123QWE,./` for accessing the campaign with code `my_campaign`.
- `ADMIN_DASHBOARD_PASSWORD=` Admin password for accessing protected paths all campaigns when logging in with
  username `admin`.
- `OWNER_NAME=` Owner name - to display in footer.
- `OWNER_LINK=` Owner link - to display in footer.
- `COMPANY_NAME=` Company name - to display in footer.
- `COMPANY_LINK=` Company link - to display in footer.

Google - `CLOUD_SERVICE=google`:

- `GOOGLE_CREDENTIALS_JSON_B64=` Content of credentials.json file in `Base64` format.
- `GOOGLE_CLOUD_STORAGE_BUCKET_FILE=` The Google cloud storage bucket to load the CSV file from.
- `GOOGLE_CLOUD_STORAGE_BUCKET_TMP_DATA=` The Google cloud storage bucket to temporarily cache
  download data. These are CSV files when making a request at e.g. `/api/v1/campaigns/{campaign_code}/data/`.

Azure - `CLOUD_SERVICE=azure`:

- `AZURE_TRANSLATOR_KEY=` The Azure translator key.
- `AZURE_STORAGE_ACCOUNT_NAME=` The Azure storage account name.
- `AZURE_STORAGE_ACCOUNT_KEY=` The Azure storage account key.
- `AZURE_STORAGE_CONNECTION_STRING=` The Azure storage connection string.
- `AZURE_STORAGE_CONTAINER_FILE=` The Azure storage container to load the CSV file from.
- `AZURE_STORAGE_CONTAINER_TMP_DATA=` The Azure storage container to temporarily cache download
  data. These are CSV files when making a request at e.g. `/api/v1/campaigns/{campaign_code}/data/`.

## System requirements

- Python 3.10 or above.

## Install

Install requirements:

```bash
pip install -r requirements.txt
```

Configure the environment variables.

### Run

```bash
python main.py
```

## Docs

You can view the docs locally at e.g. `http://127.0.0.1:8000/docs`.

## CSV file

The CSV file might contain the following columns:

- `q1_response`: Required - The response from the respondent.
- `q1_canonical_code`: Required - The category of the response.
- `alpha2country`: Required - alpha-2 code of the respondent's country.
- `age`: Optional - The respondent's age.
- `region`: Optional - The respondent's region.
- `province`: Optional - The respondent's province.
- `gender`: Optional - The respondent's gender.
- `ingestion_time`: Optional - Ingestion time of the response e.g. 2023-12-01 10:00:00.000000+00:00.
- `profession`: Optional - The respondent's profession.
- `setting`: Optional - The respondent's living setting.
- `response_year`: Optional - The year the response was collected.
- `data_source`: Optional - Source of data.

### Add another response in CSV file

`q1` refers to the question from which the respondent gave a response. To include another response add the
columns `q2_response` and `q2_canonical_code`.

## How to create a new campaign

1. Create a new config folder at `campaigns-configurations/{NEW_CONFIG_FOLDER_NAME}` (can be any name).
2. Inside the new folder create the file `config.json` (copy `config.json`
   from `campaigns-configurations/example/config.json`).
3. Fill in the configuration:
    1. `campaign_code` Required - An unique code for the campaign.
    2. `dashboard_path` Required - Path to access the dashboard in the front.
    3. `campaign_title` Required - The campaign title.
    4. `campaign_subtext` Required - The campaign subtext.
    5. `site_title` Required - Title of the dashboard.
    6. `site_description` Required - A description of the dashboard.
    7. `file` Required - This can either be a local file in the config folder, a direct link or from the cloud service
       defined in the env variables. e.g. `"file" : {"local" : "file.csv"}`
       or `"file" : {"link" : "https://example.com/file.csv"}` or `"file" : {"cloud" : "blob_name.csv"}`. The responses
       in the CSV have to be lemmatized, read step 5. If you are using `cloud`, it is necessary to set `CLOUD_SERVICE`
       and fill in the env variables for `Google` or `Azure`. Upload the CSV file at `GOOGLE_CLOUD_STORAGE_BUCKET_FILE`
       or `AZURE_STORAGE_CONTAINER_FILE`.
    8. `respondent_noun_singular`: Optional - Respondent noun singular.
    9. `respondent_noun_plural`: Optional - Respondent noun plural.
    10. `video_link` - Optional - A Link to a video related to the dashboard.
    11. `about_us_link` - Optional - Link to a page about the campaign.
    12. `questions` Optional - If there's more than one response included in the data, add the question that relates to
        it inside `config.json` at `questions` e.g. `"questions": {"q1": "Question 1", "q2" : "Question 2"}`, the user
        will be able to see the questions in the front-end and switch between responses.
    13. `parent_categories` Required - use the example data structure to build a list of categories. This is a list of
        parent-categories and each parent-category can include a list of sub-categories. In the case that there is no
        hierarchy of categories, create a parent category with `code` as an empty string and include the categories as
        its sub-categories. in the CSV file the sub-categories for responses should be added at `q1_canonical_code`.
4. Copy your CSV file to the new config folder.
5. Lemmatize the responses in the CSV file, set `file` to `{"local" : "your-csv-file-name.csv"}` and
   run `python lemmatize_responses.py my_campaign_code`, replace `my_campaign_code` with your new campaign code.

When a new campaign is successfully created, its dashboard will be accessible in the front-end using
the `dashboard_path` defined in the config.

## Translations

To allow translations with `Google Cloud Translation API` set `GOOGLE_CREDENTIALS_JSON_B64` (in `Base64` format).
For `Azure Translator` set `AZURE_TRANSLATOR_KEY`.

Set `TRANSLATIONS_ENABLED` to `True`.

### Back-end

Translations occur automatically on the fly when requesting campaign data with one of the supported languages. Will
default to English if an unsupported language code is given. Supported languages are from languages the cloud service
supports for translation.

### Front-end

To generate static translations for the front-end, create a JSON file at `front_translations/to_translate.json` if it
doesn't exist yet, and add the keys that will be used in the front-end for accessing translations and use as value the
text in English.

For example:

```json
{
  "example-text": "Lorem Ipsum"
}
```

To apply translations run:

```bash
python translate_front.py
```

Once translations have been applied, a new folder called `languages` should have been created
inside `front_translations`. Copy the `languages` folder to the front-end project at `src/app/i18n`.

*Note: Only texts that have not been translated yet will be translated and saved to `translations.json`.*

## Deployment to Google App Engine

Fork this repository and add the required environment variables to `Repository secrets` in GitHub. Add optional
environment variables if needed. These variables will be loaded into `app.yaml`. To add `{CAMPAIGN_CODE}_PASSWORD=` you
must manually add this to `Repository secrets` with the campaign code and reference it
in `.github/workflows/prod-deploy-google-app-engine.yaml` and `app.yaml`.

Inside `app.yaml` change `service` to your service name on App Engine.

For deployment, it is also required to add the following environment variables to `Repository secrets`:

- `GOOGLE_CREDENTIALS_JSON_B64=` Content of credentials.json file in `Base64` format.
- `SERVICE_NAME=` The service name in App Engine.
- `SERVICE_ACCOUNT=` The Google Cloud service account.
- `PROJECT_ID=` The Google Cloud project id.

Add/Modify `resources` in `app.yaml` as needed.

The GitHub action at `.github/workflows/prod-deploy-google-app-engine.yaml` will trigger a deployment to Google App
Engine on push or merge.

You can deploy manually from the command line using `gcloud app deploy app.yaml` (you must directly include the env
variables in `app.yaml` for this to work). You need to install Google Cloud CLI (Command Line Interface) and be
authenticated on the Google Cloud Platform service account.

## Deployment to Azure Web Apps

Fork this repository and add the required environment variables to `Application settings` in the Azure web app. Add
optional environment variables if needed.

For deployment, it is also required to add the following environment variables to `Repository secrets` in GitHub:

- `AZURE_WEBAPP_PUBLISH_PROFILE=` The publish profile of your web app.
- `AZURE_WEBAPP_NAME=` The web app name.

The GitHub action at `.github/workflows/prod-deploy-azure-webapps.yaml` will trigger a deployment to Azure Web
App on push or merge.

## Workflows

In each repository there's two workflows (To deploy to `Google` or `Azure`), make sure to only enable the correct
workflow in the repository
on GitHub: `https://docs.github.com/en/actions/using-workflows/disabling-and-enabling-a-workflow`.

## License

MIT License.