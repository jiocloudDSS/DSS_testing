import boto
import boto.s3.connection
from boto.s3.key import Key
import sys
logfile = sys.argv[1]
access_key = '0ef217eff5b146f19759532d3b6ea76a'
secret_key = '84984692b91c4795b34c1237f4040e34'

aws_access_key = 'AKIAJAQT5FMK76GBRJPQ'
aws_secret_key = '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'
conn = boto.connect_s3(
    aws_access_key_id = access_key,
    aws_secret_access_key = secret_key,
    host = "10.140.214.250",
   # host = 's3.amazonaws.com',
    is_secure=True,
    calling_format = boto.s3.connection.OrdinaryCallingFormat(),
    debug=0
    )

#conn = S3Connection(aws_access_key, aws_secret_key)

b = conn.get_bucket('dss-staging-sanity-logs')
k=b.new_key(logfile)
path="/home/obj_team/monitoring/api-sanity/" + logfile
k.set_contents_from_filename(logfile)
url=k.generate_url(1800000)
exit(url)
