#!/bin/bash

# Replace with your actual webhook URL
WEBHOOK_URL="$1"

if [ -z "$WEBHOOK_URL" ]; then
  echo "Error: Please provide your Slack webhook URL as an argument"
  echo "Usage: ./test_slack_webhook.sh YOUR_WEBHOOK_URL"
  exit 1
fi

# Send a test message
curl -X POST -H 'Content-type: application/json' --data '{
  "text": "🚀 *Test Notification*: This is a test message from your Emotional Wellness API project",
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "Emotional Wellness API Test"
      }
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Status:*\n✅ Success"
        },
        {
          "type": "mrkdwn", 
          "text": "*Environment:*\nTesting"
        }
      ]
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "This is a test message confirming your webhook is working correctly."
      }
    }
  ]
}' "$WEBHOOK_URL"

echo -e "\nTest notification sent! Check your Slack #deployments channel."
