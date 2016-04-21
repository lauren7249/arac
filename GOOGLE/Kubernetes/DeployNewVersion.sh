#!/usr/bin/env bash

echo "Make sure you have kubectl installed"

kubectl apply --record ./prime_deployment.yaml
sleep 1
kubectl get pod
sleep 1
kubectl get events -w