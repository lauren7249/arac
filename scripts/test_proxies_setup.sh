sudo apt-get install -y python-setuptools ipython git python-lxml 
sudo easy_install pip
sudo pip install flask flask-wtf flask-admin flask-sqlalchemy flask-mail flask-login flask-assets lxml redis boto python-geoip python-geoip-geolite2 
ssh-keygen -t rsa -b 4096 -C "laurentracytalbot@gmail.com"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa.pub
git@github.com:advisorconnect/prime.git
mv prime arachnid
export PYTHONPATH=~/arachnid