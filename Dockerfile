FROM acmichael/python2-onbuild:latest

RUN apt-get update && apt-get upgrade -y && apt-get clean all
RUN ["groupadd", "-g 999", "postgres"]
RUN ["useradd", "-u 999", "-g 999", "postgres"]
RUN ["chown", "postgres:postgres", "-R", "/usr/src/app"]

USER postgres

EXPOSE

ENTRYPOINT ["make"]
CMD ["run"]

USER root

