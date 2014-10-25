from redis_queue import RedisQueue
from get_redis import get_redis

#from scraper import process_request

def process_request_q(q, url):
    results = process_request(url)

    results['datetime'] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # get the result links and create jobs from
    # them if they are not finished
    for link in results['links']:
        q.push(link)

    # upload the results to s3
    key = Key(s3_bucket)
    key.key = results['url'].replace('/', '')
    key.set_contents_from_string(json.dumps(results))

    # succeed
    q.succeed(url)

def fake(url):
    print 'proessing url', url

def main():
    redis = get_redis()
    q = RedisQueue(
        redis,
        'linkedin_pending',
        'linkedin_working',
        'linkedin_fail',
        'linkedin_success',
        'linkedin_seen')

    # grab the next piece of work
    url = q.pop()

    while True:
        try:
            fake(url)
        except Exception as ex:
            q.fail(url)
            raise ex
        else:
            q.succeed(url)

        url = q.pop()

if __name__ == '__main__':
    main()
