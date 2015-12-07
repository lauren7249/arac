FROM python:2-onbuild

RUN apt-get install postgres-devel

ENTRYPOINT ["make"]
CMD ["run"]