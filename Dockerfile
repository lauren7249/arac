FROM acmichael/python2-onbuild:latest

#RUN apt-get update && apt-get upgrade -y && apt-get clean all
RUN apt-get install -y iceweasel xvfb
RUN ["groupadd", "-g 999", "postgres"]
RUN ["useradd", "-u 999", "-g 999", "postgres"]
RUN ["chown", "postgres:postgres", "-R", "/usr/src/app"]

USER postgres

EXPOSE 80
EXPOSE 443

ENTRYPOINT ["./control.sh"]
CMD ["dev_run"]

USER root

