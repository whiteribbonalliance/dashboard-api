# Dashboard API

## What does this API do?

This API is used for providing campaign data to display in the front-end dashboard. Follow the steps at
section `How to create a new campaign`. Once a new campaign was added, the data will become available through the
endpoints. For more information, continue reading the documentation below.

## Environment variables:

- `STAGE=` Required - prod or dev.
- `HOST=` Required - The host.
- `PORT=` Required - The port.
- `APP_TITLE=` Optional - App title.
- `APP_DESCRIPTION=` Optional - App description.
- `OWNER_NAME=` Optional - Owner name - to display in footer.
- `ONWER_LINK=` Optional - Owner link - to display in footer.
- `COMPANY_NAME=` Optional - Company name - to display in footer.
- `COMPANY_LINK=` Optional - Company link - to display in footer.
  campaign data. Requires Google Cloud `credentials.json` with the right permissions.
- `ACCESS_TOKEN_SECRET_KEY=` Optional - Secret key for JWT encoding - Used for all protected paths e.g. for downloading
  campaign data.
- `NEWRELIC_API_KEY=` Optional - The New Relic API key.
- `NEW_RELIC_URL=` Optional - The New Relic URL.
- `TRANSLATIONS_ENABLED=` Optional - True or False.
- `CLOUD_SERVICE=` Optional - `google` or `azure`. The cloud service will be used for translations if enabled, loading
  CSV files if you choose to do so from the cloud, and caching CSV files for downloading. Must be set if using any of
  the functionalities mentioned.
- `RELOAD_DATA_EVERY_12TH_HOUR=` Optional - Allows reloading CSV file from source every 12th hour.
- `{CAMPAIGN_CODE}_PASSWORD=` Optional - A password for accessing protected paths of a campaign
  e.g. `my_campaign_PASSWORD=123QWE,./` for accessing the campaign with code `my_campaign`.

Google:

- `GOOGLE_CLOUD_STORAGE_BUCKET_FILE=` Optional - if `google`, The Google cloud storage bucket to load the CSV file from.
- `GOOGLE_CLOUD_STORAGE_BUCKET_TMP_DATA=` Optional - if `google`, The Google cloud storage bucket to temporarily store
  download data.

Azure:

- `AZURE_TRANSLATOR_KEY=` Optional - if `azure`, The Azure translator key.
- `AZURE_STORAGE_ACCOUNT_NAME=` Optional - if `azure`, The Azure storage account name.
- `AZURE_STORAGE_CONTAINER_FILE=` Optional - if `azure`, The Azure storage container to load the CSV file from.
- `AZURE_STORAGE_CONTAINER_TMP_DATA=` Optional - if `azure`, The Azure storage container to temporarily store download
  data.
- `AZURE_STORAGE_ACCOUNT_KEY=` Optional - if `azure`, The Azure storage account key.
- `AZURE_STORAGE_CONNECTION_STRING=` Optional - if `azure`, The Azure storage connection string.

## Install

Install requirements:

```bash
pip install -r requirements.txt
```

Configure the environment variables.

Check the section `CSV file` and `How to add a new campaign` before running the API.

### Run

```bash
python main.py
```

## Docs

You can view the docs at `http://127.0.0.1:8000/docs`.

## CSV file

The CSV file might contain the following columns:

- `q1_response`: Required - The response from the respondent.
- `q1_canonical_code`: Required - The category of the response.
- `alpha2country`: Required - alpha-2 code of the respondent's country.
- `age`: Required - The respondent's age.
- `region`: Optional - The respondent's region.
- `province`: Optional - The respondent's province.
- `gender`: Optional - The respondent's gender.
- `ingestion_time`: Optional - Ingestion time of the response e.g. 2023-12-01 10:00:00.000000+00:00.
- `profession`: Optional - The respondent's profession.
- `setting`: Optional - The respondent's living setting.
- `response_year`: Optional - The year the response was collected.

`q1` refers to the question from which the respondent gave a response. To include another response add the
columns `q2_response` and `q2_canonical_code`.

## How to create a new campaign

1. Create a new config folder at `campaigns-config/{NEW_CONFIG_FOLDER_NAME}`.
2. Inside the new folder create the file `config.json` (copy `config.json` from `campaigns-config/example/config.json`).
3. Fill in the configuration:
    1. `campaign_code`: Required - An unique code for the campaign.
    2. `dashboard_path` Required - Path to access the dashboard in the front.
    3. `seo_title` Required - Title of the dashboard for SEO.
    4. `seo_meta_description` Required - A description of the dashboard for SEO.
    5. `file` Required - This can either be a local file in the config folder, a direct link or from the cloud service
       defined in the env variables. e.g. `"file" : {"local" : "file.csv"}`
       or `"file" : {"link" : "https://example.com/file.csv"}` or `"file" : {"cloud" : "blob_name.csv"}`. The responses
       in the CSV have to be lemmatized, read step 5. If you are using `cloud`, it is necessary to set `CLOUD_SERVICE`
       and fill in the env variables for `Google` or `Azure`. Upload the CSV file at `GOOGLE_CLOUD_STORAGE_BUCKET_FILE`
       or `AZURE_STORAGE_CONTAINER_FILE`.
    6. `respondent_noun_singular`: Optional - Respondent noun singular.
    7. `respondent_noun_plural`: Optional - Respondent noun plural.
    8. `video_link` - Optional - A Link to a video related to the dashboard.
    9. `about_us_link` - Optional - Link to a page about the campaign.
    10. `questions` Optional - If there's more than one response included in the data, add the question that relates to
        it inside `config.json` at `questions` e.g. `"questions": {"q1": "Question 1", "q2" : "Question 2"}`, the user
        will be able to see the questions in the front-end and switch between responses.
    11. `parent_categories` Required - use the example data structure to build a list of categories. This is a list of
        parent-categories and each parent-category can include a list of sub-categories. In the case that there is no
        hierarchy of categories, create a parent category with `code` as an empty string and include the categories as
        its sub-categories. in the CSV file the sub-categories for responses should be added at `q1_canonical_code`.
4. Copy your CSV file to the new config folder.
5. Lemmatize the responses in the CSV file, set `file` to `{"local" : "your-csv-file-name.csv"}` and
   run `python lemmatize_responses.py my_campaign_code`, replace `my_campaign_code` with your new campaign code.
6. Create translations for the front, read the `Translations` section for more information.

When a new campaign is created, its dashboard will be accessible in the front-end using the `dashboard_path` from the
config after a new build has been created in the front-end.

*As a rule of thumb, generate a new build in the front-end if any changes have been applied in the back-end.*

## Translations

To allow translations with `Google Cloud Translation API` include the Google Cloud service account's `credentials.json`
at the root of the project. For `Azure Translator` fill the env variable `AZURE_TRANSLATOR_KEY`.

Set `TRANSLATIONS_ENABLED` to `True`.

### Back-end

Translations occur automatically on the fly when requesting campaign data with one of the supported languages.

### Front-end

Create the JSON file `front_translations/to_translate.json` if it doesn't exist yet, and add the keys that will be used
in the front-end for accessing translations and use as value the text in English.

For example:

```json
{
  "example-title": "Lorem Ipsum",
  "example-subtext": "Lorem Ipsum"
}
```

`example` here refers to a campaign code.

To apply translations run:

```bash
python translate_front.py
```

*Note: When adding a new campaign, the above should be done even if translations is disabled, this is because with
translations disabled, the default language is English and the output of the translations function will contain only the
language English which is used in the front. `example` in `example-title` refers to a campaign
code. `{CAMPAIGN_CODE}-title` and `{CAMPAIGN_CODE}-subtext` are always required to be included in `to_translate.json`.*

Once translations have been applied, a new folder called `languages` should have been created
inside `front_translations`. Copy the `languages` folder to the front-end project at `src/app/i18n`.

*Note: Only texts that have not been translated yet will be translated and saved to `translations.json`.*

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
workflow in the repository
on GitHub: `https://docs.github.com/en/actions/using-workflows/disabling-and-enabling-a-workflow`.

## Legacy campaigns

For deployment of legacy campaigns.

Legacy campaigns are campaigns that were used to run this dashboard originally.

Additional environment variables:

- `LEGACY_CAMPAIGNS=` True.
- `GOOGLE_MAPS_API_KEY=` The Google Maps API key.
- `ADMIN_DASHBOARD_PASSWORD=` Admin password.