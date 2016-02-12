FROM python:2
MAINTAINER <michael@advisorconnect.co>

ENV LC_ALL en_US.utf8
ENV MAKEFLAGS -j 8
RUN apt-get autoremove -y
RUN apt-get update && \
		apt-get install -y libblas-dev libatlas-dev g++ libatlas-dev libatlas3-base libblas3gf libopenblas-dev liblapack3 liblapacke-dev liblapacke \
		fftw-dev sfftw-dev libfftw3-dev python2.7-dev libpython2.7-dev libpython-all-dev  liblapack-dev \
  		apt-utils binfmt-support gfortran postgresql-client libpq-dev libpq5 libpqxx-dev libhiredis-dev libghc-hedis-dev redis-tools locales-all \
  		libjansson4 libmatheval1 libonig2 libperl4-corelibs-perl libpgm-5.1-0 libqdbm14 libsodium13 libzmq3 lsof psmisc 
#RUN apt-get install -y iceweasel xvfb

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Add a base set of common requirements
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# Allow for new requirements to be added when a subsequent build occurs
ONBUILD COPY requirements.txt /usr/src/app/
ONBUILD RUN  pip install --upgrade pip
ONBUILD RUN  pip install --no-cache-dir -r requirements.txt

# Copy source into the app folder
ONBUILD COPY . /usr/src/app

