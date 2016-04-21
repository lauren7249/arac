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

Updating Kubernetes

  `git pull origin <branch-to-be-deployed>`
  `docker build -t gcr.io/advisorconnect-1238/aconn:<new_version_number> .`
  `gcloud docker push gcr.io/advisorconnect-1238/aconn:<new_version_number>`
  `cd uat`
  `update prime_deployment.yaml to point to new version number`
  `kubectl apply --record -f prime_deployment.yaml`


Deploying live

  `cd/uat`
  `kubectl apply --record -f prime_deployment.yaml`

Accessing a pod
  
  `kubectl get pods`
  `kubectl exec -t -i <NAME> bash`

Accessing a machine
  
  `gcloud compute ssh michael`
