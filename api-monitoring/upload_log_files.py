import boto
import boto.s3.connection
from boto.s3.key import Key
import sys
logfile = sys.argv[1]
access_key = 
secret_key = 

aws_access_key = 
aws_secret_key = 
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
