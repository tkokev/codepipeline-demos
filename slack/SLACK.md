# CodePipeline Slack Integration Demo

NOTE: This demo builds on the [CodePipeline Versioning Demo](../README.md) covered in the top level README of this repo. If you haven't already performed those steps, please do so now. They must be completed prior to continuing on with this demo. You must also already have a Slack account and be the Owner of a Workspace. Otherwise, they are free and easy to setup.

## Background

App Developers & Testers can benefit from gettings a "heads up" notification that a new App version has been deployed/released to a specific environment (Test, Stage, Prod,...). This can trigger them to perform a manual validation of a new feature before promoting the change all the way to the production version of the Application. Or it can just be a way to quickly figure out what version is on what stage of the pipeline.

Here are some facts about how we'll be interacting with Slack. In depth understanding of each is not required but check out the links if you are unfamiliar with any.
* Type of integration
  * [Slack Internal Integration](https://api.slack.com/internal-integrations)
* Method of integration
  * [Slack Webhooks](https://api.slack.com/incoming-webhooks#sending_messages)
  * More [webhook](https://en.wikipedia.org/wiki/Webhook) details
* Integration tool
  * [curl](https://curl.haxx.se/) details

## Procedures

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
   * You should see the contents of `message.json` show up within in your Slack channel!

Now lets update the Appspec file from this repo to include a new `AfterInstall` step that will send build specific information into your teams slack channel for alerting when new deploys have rolled out.

For developers, the most helpful details to see in Slack would be their last git commit comment. Here is a [conversation](https://forums.aws.amazon.com/thread.jspa?threadID=226646) about ways to grab git repo metadata.

WORK IN PROGRESS. CHECK BACK LATER. 
