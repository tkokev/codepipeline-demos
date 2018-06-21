# CodePipeline App Versioning Demo

## Overview

These instructions demonstrate how to combine AWS CodePipeline, CodeDeploy, & CodeCommit to dynamically generate and deploy a version release webpage for an application using CodeDeploy environment variables and a blue/green deploy approach.

This repo contains a minimal webpage (index.html) that represents the home page of a very simple web application, called `demo-app`, to be deployed on amazon resources using their latest Dev/Ops services. This simple website contains a single link to another minimal webpage (release.html) containing details about the `demo-app` version currently deployed. The instructions simulate one way a Dev/Ops Application Team could deploy an intial release of its `demo-app` application for customers to consume and how they can include automated versioning into the process for all future `demo-app` releases by automatically injecting CodeDeploy version related environment variables into the release.html page.

## Background

When an App Development Team first starts out it may not be known at the time whether their soon to be developed App will grow into a heavily depended upon component in a much larger Orginizational ecosystem. Because of that and short timelines, application versioning may not start off as a core focus. Sooner or later another Application Developement Team in the Orginization will start coding towards its services and/or API's. They may struggle or become frustrated during the process if they don't have a reliable way to determine what current version of `demo-app` is deployed on the Test or Production environment. To enable quicker adoption by other Teams and avoid Developer frustration, providing a few details about the deployed version on the web application (via html or API) itself will go a long way.

## Description

AWS CodeDeploy allows you to define pre, during, and post deploy actions needing performed in order for an application to be pulled from a source repo, a build artifact created, and deployment of the build artifact to a compute environment. For `demo-app`, these steps are captured in the `appspec.yml` file at the top level of this repo. Each step executes a BASH script under the `scripts` directory.

The `app_release.py` python script holds most of the magic for this demonstration. When the `appspec.yml` script executes it, it looks for static pattern in the release.html file and replaces it with variables set in the ec2 operating system by the CodeDeploy agent at time of app deploy. The CodeDeploy agent is installed on the operating system by userdata (./scripts/install_codedploy.sh) defined in the Auto Scale Group (ASG) Launch Config. One of the steps in the following procedures creates the ASG that always makes sure a minimum of one instance is always online. If not, it spins up a replacement instance.

During a deploy, a duplicate ASG is created and the latest App release is deployed to its instances. After passing all checks, an ELB that fronts the ASG, begins redirecting traffic destined to the older App version over to the new ASG. For a brief moment, traffic round robins between both of the App versions. The length of that time is adjustable. Finally, the older releases ASG and its instances are terminated once deployment is determined successful.

## Procedures

Each step below starts with the graphical method to make a change to your AWS environment followed by the AWS CLI equivalent command (for the most part). Only run one or the other but not both. If this is your first time using any of the AWS Developer service offerings (CodeDeploy, CodePipeline, CodeCommmit), it is recommended to go through the entirety using the graphical commands. Afterwards, delete everything and try only using the AWS CLI commands.

![Release Page](https://raw.githubusercontent.com/tkokev/codepipeline-demos/master/demo-app-release-site.png)


Here is some asci art showing the relationship between files in this repo and services in AWS.
```
--CodePipeline "demo-app"
    |--iam role "codepipeline-service-role"
    |   |--./aws-policies/codepipeline-service-role.json
    |--Repo: CodeCommit "pipeline-demo"
    |--Build: Jenkins "My Jenkins"
    |--Deploy: CodeDeploy
        |--iam user "demo-app-SRE"
        |   |--./aws-policies/codedeploy-user.json
        |--S3 "demo-app-<DATE>"
        |--App name "demo-app"
            |--Deploy group "demo-app-group"
                |--blue/green
                |--ASG "demo-app-asg"
                    |--group "demo-app-asg"
                    |   |--ELB "demo-app"
                    |       |--SG
                    |       |    |--name = "demo-app-elb"
                    |       |    |--ports = HTTP
                    |       |--vpc = your default vpc
                    |
                    |--LC "demo-app-lc"
                        |--t2.micro
                        |--spot
                        |--$.004
                        |--iam role: "demo-app-ec2-instance-profile"
                        |   |--Policy: "demo-app-ec2-permisions"
                        |      |--./aws-policies/codedeploy-ec2.json
                        |--user data: ./install_codedeploy.sh
```
1. if you don't already have an AWS VPC, set up a generic one in using the `Start VPC Wizard` button found at <https://console.aws.amazon.com/vpc/home?region=us-east-1#>
1. create a codecommit repo
    * name = demo-app
    * source = sns topic
        * new
            * name = codecommit_pipeline-demo
            * add files = https
            * Linux
    ```bash
    aws codecommit create-repository --repository-name demo-app --repository-description "Demo App from github.com/tkokev/codepipeline-demos"
    ```
1. go to aws iam and add `AWSCodeCommitFullAccess` to the user account that will be committing code (<https://docs.aws.amazon.com/codecommit/latest/userguide/setting-up-gc.html>) OR
1. create an user in iam with permissions to perform all the following steps
    * name = demo-app-SRE
        * policies
            * ./aws-policies/code-deploy-user.json
    ```bash
    # create user policies
    arn=$(aws iam create-policy --policy-name demo-app-SRE --policy-document file://aws-policies/codedeploy-user.json --query "Policy.Arn" --output text)
    # create user and attach policies
    aws iam create-user --user-name demo-app-user1
    aws iam attach-user-policy --user-name demo-app-user --policy-arn $arn
    ```
1. upload your users public key using the `Upload SSH public key` button on the Security credential tab. (https://docs.aws.amazon.com/codecommit/latest/userguide/setting-up-ssh-unixes.html)
    * if you only have a private key, use this command to extract the public key.
    `sh-keygen -y -f ~/.ssh/userprivatekey.pem`
1. copy the `SSH key id` value
1. add the below to your ~/.ssh/config file pasting the `SSH key id`
    ```bash
    Host git-codecommit.*.amazonaws.com
    User APKAEIBAERJR2EXAMPLE
    IdentityFile ~/.ssh/userprivatekey.pem
    ```
1. run these commands on dev box used to pull down the contents of this GitHub repo
    ```bash
    git clone https://github.com/tkokev/codepipeline-demos.git
    ```
1. copy the contents of this repo into your CodeCommit repo for later use
    ```bash
    cd codepipeline-demos
    git remote add codecommit ssh://git-codecommit.us-east-1.amazonaws.com/v1/repos/demo-app
    git push codecommit
    ```
1. create an s3 bucket for deploygroup
    * demo-app-DATE
    ```bash
    aws s3 mb s3://demo-app-$(date +%Y%m%d)
    ```
1. create sg for elb
    * name = demo-app-elb
    * ports = http
    ```bash
    VPCID=changeme
    sgid=$(aws ec2 create-security-group --group-name demo-app-elb --description demo-app-elb --vpc-id $VPCID --output text)
    aws ec2 authorize-security-group-ingress --group-id $sgid --protocol tcp --port 80 --cidr "0.0.0.0/0"
    ```
1. create elb

    After creating the ELB keep its A Record handy. This is the address you will browse to when checking out the deployed `demo-app` web application after all the steps below are completed.
    * type = http https
    * name = demo-app
    * vpc = your default vpc
    * tags
        * key/value = Name/demo-app-elb
    * sg = demo-app-elb
    * target group = new
    * target name = demo-app
    * register targets = leave empty
    ```bash
    VPCID=changeme
    subnetids=( $(aws ec2 describe-subnets --filters Name=tag-value,Values=*pub* --query '*[].SubnetId' --output text) )
    elbarn=$(aws elbv2 create-load-balancer --name demo-app --subnets ${subnetids[@]} --security-groups $sgid --query *[].LoadBalancerArn --output text)
    targetarn=$(aws elbv2 create-target-group --name demo-app --protocol HTTP --port 80 --vpc-id $VPCID)
    aws elbv2 create-listener --load-balancer-arn $elbarn --protocol HTTP --port 80 --default-actions Type=forward,TargetGroupArn=$targetarn --query *[].TargetGroupArn
    ```
1. create iam policies, profiles & roles
    * Role Name = demo-app-codedeploy-service-role
        * Policies
            * ./aws-policies/codedeploy-sts.json
            * AWSCodeDeployRole
    * Role Name = demo-app-ec2-instance-profile
        * Policies
            * ./aws-policies/role-policy-document.json
            * ./aws-policies/codedeploy-ec2.json
    ```bash
    # Service Role https://docs.aws.amazon.com/codedeploy/latest/userguide/getting-started-create-service-role.html
    arn=$(aws iam create-role --role-name demo-app-codedeploy-service-role --assume-role-policy-document file://aws-policies/codedeploy-sts.json --query "Role.Arn" --output text)
    aws iam attach-role-policy --role-name demo-app-codedeploy-service-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSCodeDeployRole
    # Instance Role & Profile https://docs.aws.amazon.com/codedeploy/latest/userguide/getting-started-create-iam-instance-profile.html
    aws iam create-role --role-name demo-app-ec2-instance-profile --assume-role-policy-document file://aws-policies/role-policy-document.json
    aws iam put-role-policy --role-name demo-app-ec2-instance-profile --policy-name demo-app-ec2-permissions --policy-document file://aws-policies/codedeploy-ec2.json
    aws iam create-instance-profile --instance-profile-name demo-app-ec2-instance-profile
    aws iam add-role-to-instance-profile --instance-profile-name demo-app-ec2-instance-profile --role-name demo-app-ec2-instance-profile
    ```
1. create iam role
    * name = demo-app-codedeploy
    * managed policies =
        * name = codedeploy.json
1. create security group "demo-app-elb"
    * ports = 80/tcp inbound
1. create launch config or create asg
    * ami = aws marketplace
    * search "centos" to find "CentOS 7 (x86_64) - with Updates HVM"
    * type = t2.micro
    * lc name = demo-app-lc
    * iam role = demo-app-codedeploy
    * advanced
        * user data = ./install_codedeploy.sh
        * ip = assign public ip
    * sda1 delte on termination
    * sg = "demo-app-elb"
    * GROUP NAME = demo-app
    * size = 2
    * network = your default vpc
    * subnets = your pub subs
    * keep at orig size
    * commands *replace capitalized words with your values
    * key/value  = Name/demo-app-asg
    ```bash
    imageid=$(aws ec2 describe-images --filter Name=owner-id,Values=679593333241 Name=name,Values="CentOS Linux 7 x86_64 HVM *" --query "*[].{DATE:CreationDate,ID:ImageId}" --output text | sort | cut -f2 | tail -1)
    sgid=$(aws ec2 describe-security-groups --filters Name=group-name,Values=demo-app-elb --query '*[].GroupId' --output text)

    aws autoscaling create-launch-configuration --image-id $imageid --key-name YOURAWSSSHKEYNAME --user-data file://scripts/install_codedeploy.yml --instance-type t2.micro --security-groups $sgid --block-device-mappings file://disk.yml --launch-configuration-name demo-app-lc --iam-instance-profile demo-app-ec2-instance-profile

    subnetids=( $(aws ec2 describe-subnets --filters Name=tag-value,Values=*pub* --query '*[].SubnetId' --output text) )

    aws autoscaling create-auto-scaling-group --auto-scaling-group-name demo-app-asg --min-size 1 --max-size 2 --launch-configuration-name demo-app-lc --vpc-zone-identifier $(echo ${subnetids[@]} | tr ' ' ',')
    ```
1. create codedeploy app <https://docs.aws.amazon.com/codedeploy/latest/userguide/getting-started-codedeploy.html>
    * name = demo-app
    * compute = ec2
    * deploy group = demo-app-bluegreen
    * deploy type = blue/green
    * env config 
        * app location = auto copy asg
        * asg name = demo-app-asg
        * elb = demo-app
    rollback = when dep fails
    * service role arn = arn of demo-app-codedeploy-service-role created above
    ```bash
    arn=$(aws iam get-role --role-name demo-app-codedeploy-service-role --query "Role.Arn" --output text)

    aws deploy create-application --application-name demo-app
    #
    aws deploy create-deployment-group --application-name demo-app --deployment-group-name demo-app-bluegreen --deployment-style deploymentType=BLUE_GREEN,deploymentOption=WITH_TRAFFIC_CONTROL --blue-green-deployment-configuration 'terminateBlueInstancesOnDeploymentSuccess={action=TERMINATE,terminationWaitTimeInMinutes=10},deploymentReadyOption={actionOnTimeout="CONTINUE_DEPLOYMENT",waitTimeInMinutes=0},greenFleetProvisioningOption={action="COPY_AUTO_SCALING_GROUP"}' --auto-scaling-groups demo-app-asg --load-balancer-info targetGroupInfoList=[{name=demo-app}] --auto-rollback-configuration enabled=true,events="DEPLOYMENT_FAILURE" --service-role-arn $arn

    #this can be used to see the resulting config: aws deploy get-deployment-group --deployment-group-name demo-app-bluegreen --application-name demo-app

    #deploy build to test new configs
    aws deploy push --application-name demo-app --s3-location s3://demo-app-$(date +%Y%m%d)/demo-app --source .
    aws deploy create-deployment --application-name demo-app --s3-location bucket=demo-app-$(date +%Y%m%d),key=demo-app,bundleType=zip,eTag=FOO --deployment-group-name demo-app-bluegreen --deployment-config-name CodeDeployDefault.OneAtATime --description test-the-new-app
    ```
1. prep the codepipeline JSON file with your account specifics
    ```bash
    ACC_NUM=$(aws sts get-caller-identity --output text --query 'Account')
    sed -i "s/YOURACCOUNTNUMBER/$ACC_NUM/g" demo-app-pipeline.json
    sed -i "s/DATE/$(date +%Y%m%d)/g" demo-app-pipeline.json
    ```
1. Commit these changes into your CodeCommit repo
    ```bash
    git add demo-app-pipeline.json
    git commit -m"add my unique VPC settings to pipeline config"
    git push codecommit
    ```
1. create codepipeline
    * name = demo-app
    * source = codecommit
    * repo = demo-app
    * branch = master
    * build provider = add jenkins
    * provider name = work_jenkins
    * url = blah.com
    * project name = demo-app
    * deploy provider = codedeploy
    * app name = demo-app
    * deploy group = demo-app-group
    * role name = codepipeline-service-role
    * commands (replace capitalized words in the below referenced demo-app-pipeline.json file to your unique values)
    ```bash
    aws iam create-role --role-name codepipeline-service-role --assume-role-policy-document file://aws-policies/codepipeline-service-role.json
    aws codepipeline create-pipeline --cli-input-json file://demo-app-pipeline.json
    ```
1. Setup CodePipeline to deploy when new code is commited to demo-app codecommit.
    * browse to the AWS Web Console and select edit next to your demo-app in CodePipeline
    * Select the pencil next to Source to edit that stage
    * scroll down to change detection options and expand it
    * with the Use Amazon CloudWatch Event option selected, click the Update button. this will setup an SNS topic and cloudwatch events to start your piipeline when new code is pushed into your demo-app codecommit repo.

By now, your pipeline should be performing its initial deploy of your application onto a fresh instance within the ASG fronted by your ELB. If it's far enough along in the process, you should be able to browse to your ELB and see the index.html file being served by the instances apache webserver. If so, click the release hyperlink and you should see some details about the specific version of the app. If not, watch the deploy status each step along the way by browsing to CodePipeline and selecting the `details` link in the Deploy stage. 

# More demo topics coming soon...

* Deploy the above AWS CodePipeline "demo-app" using Hashicorps [TERRAFORM](terraform/TERRAFORM.md) [Infrastructure as Code tool](https://www.terraform.io/#writ) and its [AWS Provider](https://www.terraform.io/docs/providers/aws/)
* To see how to add Slack notifications, see [SLACK](slack/SLACK.md)
* For auto merging dev to master after passing tests, see [MERGE](merge/MERGE.md)
* Integrate with [AWS Config](awsconfig/AWSCONFIG.md)
