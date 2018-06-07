# CodePipeline Slack Integration Demo

This demo builds on the "Versioning Demo" in README.md of this repo. If you haven't already performed the steps captured in README.md, do so now. They must be completed prior to continuing on with this demo.

WORK IN PROGRESS. CHECK BACK LATER. 

* Type of integration
  * [Internal Integration](https://api.slack.com/internal-integrations)
* Method
  * [Webhooks](https://api.slack.com/incoming-webhooks#sending_messages)
    * curl -X POST -H 'Content-type: application/json' --data @slack/message.json https://hooks.slack.com/services/
