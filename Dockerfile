FROM python:2

RUN apt-get autoremove -y
RUN apt-get update && \
		apt-get install -y libblas-dev libatlas-dev g++ libatlas-dev libatlas3-base libblas3gf libopenblas-dev liblapack3 liblapacke-dev liblapacke \
		fftw-dev sfftw-dev libfftw3-dev python2.7-dev libpython2.7-dev libpython-all-dev  liblapack-dev \
  		apt-utils binfmt-support gfortran


RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

ENTRYPOINT ["make"]
CMD ["run"]
