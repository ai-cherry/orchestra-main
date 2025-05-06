# PubSub configuration for development environment

module "pubsub" {
  source = "../../modules/pubsub"
  
  project_id = var.project_id
  region     = var.region
  environment = "dev"
  
  # Use the service account from the secure credentials module
  service_account_email = module.secure_credentials.service_account_emails["orchestrator"]
  
  # Define topics specific to agent communication
  topics = {
    "agent-events" = {
      labels = {
        purpose = "agent-communication"
      }
    },
    "agent-tasks" = {
      labels = {
        purpose = "task-distribution"
      }
    },
    "agent-results" = {
      labels = {
        purpose = "task-results"
      }
    },
    "agent-memory" = {
      labels = {
        purpose = "memory-updates"
      },
      message_retention_duration = "172800s" # 48 hours
    },
    "agent-workflow" = {
      labels = {
        purpose = "workflow-state-changes"
      }
    }
  }
  
  # Define subscriptions for each topic
  subscriptions = {
    "agent-events-sub" = {
      topic = "agent-events"
      labels = {
        purpose = "agent-communication"
      },
      enable_message_ordering = true,
      filter = "attributes.event_type = \"agent_message\""
    },
    "agent-tasks-sub" = {
      topic = "agent-tasks"
      labels = {
        purpose = "task-distribution"
      },
      dead_letter_topic = "agent-events",
      max_delivery_attempts = 5
    },
    "agent-results-sub" = {
      topic = "agent-results"
      labels = {
        purpose = "task-results"
      }
    },
    "agent-memory-sub" = {
      topic = "agent-memory"
      labels = {
        purpose = "memory-updates"
      },
      message_retention_duration = "604800s" # 7 days
    },
    "agent-workflow-sub" = {
      topic = "agent-workflow"
      labels = {
        purpose = "workflow-state-changes"
      },
      enable_message_ordering = true
    }
  }
}

# Output PubSub topic and subscription names
output "pubsub_topic_names" {
  description = "The names of the created PubSub topics"
  value       = module.pubsub.topic_names
}

output "pubsub_subscription_names" {
  description = "The names of the created PubSub subscriptions"
  value       = module.pubsub.subscription_names
}