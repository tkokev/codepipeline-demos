# CodePipeline Slack Integration Demo

NOTE: This demo builds on the "Versioning Demo" in README.md of this repo. If you haven't already performed the steps captured in README.md, do so now. They must be completed prior to continuing on with this demo.

App Developers & Testers can benefit from gettings a "heads up" notification that a new App version has been deployed/released to a specific environment (Test, Stage, Prod,...). This can trigger them to perform a manual validation of a new feature before promoting the change all the way to the production version of the Application. Or it can just be a way to quickly figure out what version is on what stage of the pipeline.

Some facts about how we'll be interacting with Slack.
* Type of integration
  * [Internal Integration](https://api.slack.com/internal-integrations)
* Method
  * [Webhooks](https://api.slack.com/incoming-webhooks#sending_messages)
* Tool
  * [curl](https://curl.haxx.se/)

1. Using a web browser, log into the [Slack workspace](https://slack.com/signin) where you want AWS CodePipeline to send notifications
1. Browse to https://api.slack.com
1. Select the option to create a New App
   1. Name = `pipeline`
1. Select `Incoming Webhooks` and enable it
1. Select `Add new webhook to workspace`
1. Choose a channel and select `Authorize`
1. Take down your webhook URL
1. Test your webhook using the [message.json](slack/message.json) file in this repo by issuing the command below from your development workstation
```
curl -X POST -H 'Content-type: application/json' --data @message.json https://hooks.slack.com/services/<YOUR-UNIQUE-WEBHOOK-VALUE>
```

You should see the contents of `message.json` show up within in your Slack channel!

Now lets update the Appspec file from this repo to include a new `AfterInstall` step that will send build specific information into your teams slack channel for alerting when new deploys have rolled out.

WORK IN PROGRESS. CHECK BACK LATER. 
