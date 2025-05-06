# Outputs for the PubSub module

output "topic_names" {
  description = "The names of the created PubSub topics"
  value = {
    for k, v in google_pubsub_topic.topics : k => v.name
  }
}

output "subscription_names" {
  description = "The names of the created PubSub subscriptions"
  value = {
    for k, v in google_pubsub_subscription.subscriptions : k => v.name
  }
}

output "topic_ids" {
  description = "The fully-qualified IDs of the created PubSub topics"
  value = {
    for k, v in google_pubsub_topic.topics : k => v.id
  }
}

output "subscription_ids" {
  description = "The fully-qualified IDs of the created PubSub subscriptions"
  value = {
    for k, v in google_pubsub_subscription.subscriptions : k => v.id
  }
}