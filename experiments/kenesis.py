import argparse

from boto import kinesis

def main(put=False, read=False):
    print kinesis.regions()

    connection = kinesis.layer1.KinesisConnection()

    if put:
	connection.put_record('arachnid', 'test1', '0')

    desc = connection.describe_stream('arachnid')
    
    shard = desc['StreamDescription']['Shards'][0]
    shard_id	= shard['ShardId']
    first_seq	= shard['SequenceNumberRange']['StartingSequenceNumber']
    if read:

	shard_iterator = connection.get_shard_iterator('arachnid', shard_id,
	'TRIM_HORIZON')#, first_seq)
	print 'shard iterator', shard_iterator

	shard_iterator = shard_iterator['ShardIterator']
	total_shards = 0
	records = []
	while total_shards < 5:
	    get_records = connection.get_records(shard_iterator)
	    shard_iterator = get_records['NextShardIterator']
	    #print get_records
	    records += get_records['Records']
	    total_shards+=1

	print 'Records',records
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--put', action='store_true')
    parser.add_argument('--read', action='store_true')

    args = parser.parse_args()

    main(put=args.put, read=args.read)
