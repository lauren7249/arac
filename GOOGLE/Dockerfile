FROM acmichael/python2-onbuild:latest
MAINTAINER michael@advisorconnect.co

RUN apt-get update && apt-get upgrade -y && apt-get clean all
#RUN ["groupadd", "-g 999", "postgres"]

RUN pip install --upgrade --no-cache six grpcio gcloud
EXPOSE 80
EXPOSE 443

ENTRYPOINT ["./control.sh"]
CMD ["dev_run"]

USER root

# @formatter:off
LABEL co.advisorconnect.repo=gcr.io/advisorconnect-1238/aconn co.advisorconnect.commit=COMMIT-- co.advisorconnect.branch=BRANCH--
# @formatter:on