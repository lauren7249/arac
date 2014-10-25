import argparse
from get_redis import get_redis
from redis_queue import RedisQueue

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')

    args = parser.parse_args()

    redis = get_redis()
    q = RedisQueue(redis, 'linkedin')

    q.push(args.url)

if __name__ == '__main__':
    main()

