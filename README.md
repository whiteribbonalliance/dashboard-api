# Dashboard API

## What does this API do?

This API is used for providing campaign data to display in a dashboard. To add a new campaign you can create a new
configuration for the campaign with the required data and run the API, the data will become immediately available
through the endpoints. For more information on how to do this, continue reading the documentation below.

## Environment variables:

- `STAGE=` prod or dev.
- `HOST=` The host.
- `PORT=` The port.
- `APP_TITLE=` App title.
- `APP_DESCRIPTION=` App description.
- `GOOGLE_CLOUD_STORAGE_BUCKET_NAME=` Optional - Bucket name where generated CSV files can be stored for downloading
  campaign data. Requires Google Cloud `credentials.json` with the right permissions.
- `ACCESS_TOKEN_SECRET_KEY=` Optional - Secret key for JWT encoding - Used for all protected paths e.g. for downloading
  campaign data.
- `TRANSLATIONS_ENABLED=` Optional - True or False. If True, requires Google Cloud `credentials.json` with the right
  permissions.
- `NEWRELIC_API_KEY=` Optional - The New Relic API key.
- `NEW_RELIC_URL=` Optional - The New Relic URL.

## install

Install requirements:

```bash
pip install -r requirements.txt
```

Configure the environment variables. To allow translations with `Google Cloud Translation API` include the Google Cloud
service account's `credentials.json` at the root of the project and set `TRANSLATIONS_ENABLED` to `True`.

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

1. Create a new config folder at `campaigns-config/[NEW_CONFIG_FOLDER_NAME]`.
2. Inside the new folder create the file `config.json` (copy `config.json`
   from `campaigns-config/example/config.json`).
3. Fill in the configuration:
    1. `campaign_code`: Required - An unique code for the campaign.
    2. `password`: Optional - A password for accessing protected paths of a campaign.
    3. `dashboard_path` Required - Path to access the dashboard in the front.
    4. `dashboard_name` Required - A name for the dashboard.
    5. `seo_title` Required - Title of the dashboard for SEO.
    6. `seo_meta_description` Required - A description of the dashboard for SEO.
    7. `file` Required - The CSV filename.
    8. `file_link` Optional - A direct link to the CSV file. `file_link` will be prioritized over `file`.
    9. `respondent_noun_singular`: Optional - Respondent noun singular.
    10. `respondent_noun_plural`: Optional - Respondent noun plural.
    11. `video_link` - Optional - A Link to a video related to the dashboard.
    12. `about_us_link` - Optional - Link to a page about the campaign.
    13. `questions` Optional - If there's more than one response included in the data, add the question that relates to
        it inside `config.json` at `questions` e.g. `"questions": {"q1": "Question 1", "q2" : "Question 2"}`, the user
        will be able to see the questions in the front-end and switch between responses.
    14. `parent_categories` Required - use the example data structure to build a list of categories. This is a list of
        parent-categories and each parent-category can include a list of sub-categories. In the case that there is no
        hierarchy of categories, create a parent category with `code` as an empty string and include the categories as
        its sub-categories.
4. Copy your CSV file to the new config folder.
5. The final step is to lemmatize the responses in the CSV file, do so by running `python lemmatize_responses.py`. To
   only lemmatize a specific campaign you can run `python lemmatize_responses.py my_campaign_code`.
6. Optional - If you wish to use a link instead to load the CSV file, after lemmatizing the data, upload the CSV
   file to your hosting of choice and add the direct link at `file_link` inside `config.json`. `file_link` will be
   prioritized over `file`.

When a new campaign is created, its dashboard will be accessible in the front-end using the `dashboard_path` from the
config after a build has been created in the front-end. If the configuration is updated, a new build is required in the
front-end to reflect the changes.

## Translations

To allow translations with `Google Cloud Translation API` include the Google Cloud service account's `credentials.json`
at the root of the project and set `TRANSLATIONS_ENABLED` to `True`.

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
python translate_front.py
```

Once translations have been applied, a new folder called `languages` should have been created
inside `front_translations`. Copy the `languages` folder to the front-end project at `src/app/i18n`.

*Note: Only texts that have not been translated yet will be translated and saved to `translations.json`.*

## PMNCH - Azure deployment

Additional environment variables:

- `ONLY_PMNCH=` True.
- `AZURE_TRANSLATOR_KEY=` The Azure translator key.
- `AZURE_STORAGE_ACCOUNT_NAME=` The Azure storage account name.
- `AZURE_STORAGE_ACCOUNT_KEY=` The Azure storage account key.
- `AZURE_STORAGE_CONNECTION_STRING=` The Azure storage connection string.

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

Additional environment variables:

- `ONLY_LEGACY_CAMPAIGNS=` True.
- `GOOGLE_MAPS_API_KEY=` The Google Maps API key.
