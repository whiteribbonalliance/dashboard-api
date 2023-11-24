"""
Export PMNCH data from BigQuery to a Pickle file.
"""

from app.services import google_bigquery_interactions

print("Downloading and exporting pmn01a to a Pickle file...")

google_bigquery_interactions.export_pmn01a_data_to_pkl()

print("Export complete")
