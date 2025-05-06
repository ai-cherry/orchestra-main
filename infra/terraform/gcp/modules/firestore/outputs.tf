output "database_id" {
  description = "ID of the Firestore database"
  value       = google_firestore_database.database.id
}

output "database_name" {
  description = "Name of the Firestore database"
  value       = google_firestore_database.database.name
}
