from app.services import bigquery_interactions

print("Downloading and exporting pmn01a to CSV...")

bigquery_interactions.export_pmn01a_data_to_csv()

print("Export complete")
