#!/usr/bin/python

import os

strToSearch="<h2>This application was deployed using AWS CodeDeploy.</h2>"

strToReplace="<h2>This application was deployed using the " + os.environ['APPLICATION_NAME'] + " AWS CodeDeploy application's " + os.environ['DEPLOYMENT_GROUP_NAME'] + " deployment group via deployment group ID " + os.environ['DEPLOYMENT_GROUP_ID'] +  " generated during a " + os.environ['LIFECYCLE_EVENT'] + " lifecycle event script with revision ID " + os.environ['DEPLOYMENT_ID'] + ".</h2>"

fp=open("/var/www/html/release.html","r")
buffer=fp.read()
fp.close()

fp=open("/var/www/html/release.html","w")
fp.write(buffer.replace(strToSearch,strToReplace))
fp.close()