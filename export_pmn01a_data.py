"""
Export PMNCH data from BigQuery to a CSV file.
"""

from app.services import google_bigquery_interactions

print("Downloading and exporting pmn01a to CSV...")

google_bigquery_interactions.export_pmn01a_data_to_csv()

print("Export complete")
