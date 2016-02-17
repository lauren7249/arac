#  WELCOME TO ADVISORCONNECT ##

## Setting up dev environment

1. Updating Test Server

Make your changes and push up to git, then ssh into the server and run the following commands:

  `cd tests/prime/`

  `git pull origin master`

  `cd uat`

  `docker-compose down`

  `docker-compose build`

  `docker-compose up -d`

2. To Log into the docker container to check the logs

  `docker ps to find the prime container hash`
  `docker exec -t -i <hashcode here> /bin/bash`
