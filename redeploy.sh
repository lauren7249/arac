curdir=$(basename "$PWD")
docker exec "$curdir"_db_1 pg_dump arachnid -U arachnid > mydb.dump
docker-compose down
docker-compose build
docker-compose up -d