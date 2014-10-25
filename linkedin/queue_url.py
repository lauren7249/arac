import argparse
from get_redis import get_redis
from redis_queue import RedisQueue

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')

    args = parser.parse_args()

    redis = get_redis()
    q = RedisQueue(
        redis,
        'linkedin_pending',
        'linkedin_working',
        'linkedin_fail',
        'linkedin_success',
        'linkedin_seen')

    q.push(args.url)

if __name__ == '__main__':
    main()

