#  WELCOME TO ADVISORCONNECT ##

## Setting up dev environment

1. Updating Test Server

Make your changes and push up to git, then ssh into the server and run the following commands:

  `cd tests/prime/`
  `git pull origin master`
  `cd uat`
  `docker-compose build`
  `docker-compose up`
