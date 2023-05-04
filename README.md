# What Women Want API

Where is the URL?

https://www-api-dot-deft-stratum-290216.uc.r.appspot.com/docs

## Continuous integration

This API is built automatically by Github actions.

The Docker container is pushed to Google Container Registry.

Then it is deployed to Google App Engine using a Flex environment (see `app.yaml`).

See [/docs/docs.pdf](/docs/docs.pdf).

## Efficiency

Survey responses data is submitted to BigQuery in batches bu the background thread each N seconds.

## Monitoring

The API is monitored using NewRelic. On every batch insertion, number of rows is logged to NewRelic. 
If an operation fails, survey objects that did not make it to BigQuery are recorded as additional attributes of respective log entries, so that they don't get lost.