from run_redis_scraper import process_request_job

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--url')

    args = parser.parse_args()

    process_request_job.delay(args.url)


