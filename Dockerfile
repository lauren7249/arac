FROM acmichael/python2-onbuild:latest

RUN ["groupadd", "-g 999", "postgres"]
RUN ["useradd", "-u 999", "-g 999", "postgres"]
RUN ["chown", "postgres:postgres", "-R", "/usr/src/app"]

USER postgres
ENTRYPOINT ["make"]
CMD ["test"]
