import argparse
from redis_queue import RedisQueue

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')

    args = parser.parse_args()

    q = RedisQueue('linkedin')

    q.push(args.url)

if __name__ == '__main__':
    main()

