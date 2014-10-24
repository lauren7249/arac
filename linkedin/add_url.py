import argparse

from run_redis_scraper import process_request_job

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')

    args = parser.parse_args()

    process_request_job.delay(args.url)

if __name__ == '__main__':
    main()

