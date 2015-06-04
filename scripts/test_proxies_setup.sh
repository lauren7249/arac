sudo apt-get install -y python-setuptools ipython git python-lxml vim

sudo easy_install pip

sudo pip install flask flask-wtf flask-admin flask-sqlalchemy flask-mail flask-login flask-assets lxml redis boto python-geoip python-geoip-geolite2 tinys3 eventlet

ssh-keygen -t rsa -b 4096 -C "laurentracytalbot@gmail.com"

eval "$(ssh-agent -s)"
chmod 400 ~/.ssh/id_rsa.pub
ssh-add ~/.ssh/id_rsa.pub
KEY=$(cat ~/.ssh/id_rsa.pub)
curl -u "lauren7249:tr1bul@tion" --data '{"title":"test-key","key":"'"$KEY"'"}' https://api.github.com/user/keys
git clone git@github.com:advisorconnect/prime.git

mv prime arachnid

echo "export PYTHONPATH=~/arachnid" >> ~/.bashrc
source ~/.bashrc