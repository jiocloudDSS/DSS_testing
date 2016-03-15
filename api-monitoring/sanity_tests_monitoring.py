import os
import sys
import time
import math
import dssSanityLib
from boto.s3.key import Key
from filechunkio import FileChunkIO

############### MAX BUCKET LIMIT ###################

def bucketSanity():

    ## Create five buckets
    dssSanityLib.whisper("Creating buckets and putting objects in them...")
    bucketpref = dssSanityLib.getsNewBucketName()
    dssSanityLib.createMaxBuckets(1, bucketpref)

    ## Bucket name conflict during creation
    #dssSanityLib.whisper("Trying to create a bucket with name conflict...")
    #userObj = dssSanityLib.getConnection(1) ## Different user
    #buck_str = bucketpref + '1'
    #try:
        #b = userObj.create_bucket(buck_str)
        #print "Error: Unexpectedly created bucket " + buck_str
        #return -1
    #except:
    #    print "Expected failure: " + str(sys.exc_info())

    ## Delete all buckets
    try:
        userObj = dssSanityLib.getConnection()
        dssSanityLib.whisper("Deleting the test buckets...")
        dssSanityLib.cleanupUser(userObj, bucketpref)
    except:
        print "Unexpected failure: " + str(sys.exc_info())
        return -1
    return 0

####################################################

############### MULTI PART UPLOAD ##################

def multipartObjectUpload():
    result = 0
    dssSanityLib.whisper("Making bucket and listing...")
    userObj = dssSanityLib.getConnection()
    bucketpref = dssSanityLib.getsNewBucketName()
    b = userObj.create_bucket(bucketpref)
    #dssSanityLib.listBucket(userObj, "User")

    source_path = dssSanityLib.MULTIPART_LARGE_FILE
    source_size = os.stat(source_path).st_size
    chunk_size = 5242880 ## 5 mb
    #chunk_size = 1048576  ## 1 mb
    chunk_count = int(math.ceil(source_size / float(chunk_size)))

    b1 = userObj.get_bucket(bucketpref)
    dssSanityLib.whisper("Got bucket: " + str(b1))
    try:
        mp = b1.initiate_multipart_upload(os.path.basename(source_path))
        for i in range(chunk_count):
            dssSanityLib.whisper("Uploading chunk: " + str(i))
            offset = chunk_size * i
            bytes = min(chunk_size, source_size - offset)
            with FileChunkIO(source_path, 'r', offset=offset, bytes=bytes) as fp:
                mp.upload_part_from_file(fp, part_num=i + 1)
        mp.complete_upload()
    except:
        print "Unexpected error during multipart upload: ", sys.exc_info()
        result = -1

    dssSanityLib.cleanupUser(userObj, bucketpref)
    return result

####################################################

#################### DNS TESTS ####################

def dnsNamesTest():
    userObj = dssSanityLib.getConnection()
    result = 0
    longSixtyChars = 'a123456789a123456789a123456789a123456789a123456789a123456789'
    longTFTchars = longSixtyChars + 'qwe'
    try:
        userObj.create_bucket(longTFTchars)
        userObj.delete_bucket(longTFTchars)
        print "Able to create bucket with 63 chars in name"
    except:
        print "Failed to create or delete a valid bucket name"
        print "Unexpected error: ", sys.exc_info()
        return -1

    try:
        badName = longTFTchars + 'abc'
        userObj.create_bucket(badName)
        print "Unexpectedly created bucket with illegally long name"
        dssSanityLib.listBucketNum(userObj, "user")
       # dssSanityLib.listBucket(userObj, "user")
        userObj.delete_bucket(badName)
        result = -1
    except:
        print "Expected failure in creating 66 char bucket name"
        print "Expected error: ", sys.exc_info()

    try:
        badName = 'Abc'
        userObj.create_bucket(badName)
        print "Unexpectedly created bucket with capital letter name"
        dssSanityLib.listBucketNum(userObj, "user")
        #dssSanityLib.listBucket(userObj, "user")
        userObj.delete_bucket(badName)
        result = -1
    except:
        print "Expected failure in creating bucket name with CAPS"
        print "Expected error: ", sys.exc_info()
        #return -1#<<<<<<
    try:
        badName = 'bc/'
        userObj.create_bucket(badName)
        print "Unexpectedly created bucket with slash in name"
        dssSanityLib.listBucketNum(userObj, "user")
        #dssSanityLib.listBucket(userObj, "user")
        userObj.delete_bucket(badName)
        result = -1
    except:
        print "Expected failure in creating bucket name with slash"
        print "Expected error: ", sys.exc_info()

    return result

####################################################

################ PUBLIC URL TESTS ##################

def publicUrlTest():
    result = 0
    userObj = dssSanityLib.getConnection()
    bucketpref = dssSanityLib.getsNewBucketName()
    b1 = userObj.create_bucket(bucketpref)

    k = Key(b1)
    k.key = 'userObj1'
    k.set_contents_from_string('Data of URL object')

    m = Key(b1)
    m.key = 'userObj1'
    urlname = m.generate_url(1000)
    print "\nThe userObj URL is: " + str(urlname)
    urlname = b1.generate_url(1000)
    print "\nThe bucket URL is: " + str(urlname)

    for i in range(1, 3):
        time.sleep(1)
        if i % 5 == 0:
            print str(2 - i) + " Seconds left before Obj deletion"
    m.delete()
    print "Object deleted\n"

    for i in range(1, 3):
        time.sleep(1)
        if i % 5 == 0:
            print str(2 - i) + " Seconds left before bucket deletion"
    userObj.delete_bucket(bucketpref)
    print "Bucket deleted\n"

    return result

####################################################

###################### MAIN ########################

def main(argv):

    ## PARAM OVERRIDES
    dssSanityLib.MULTIPART_LARGE_FILE = '/boot/initrd.img-3.19.0-25-generic' # Need a large file to upload in multiparts.
    dssSanityLib.GLOBAL_DEBUG = 1                               # The lib supresses debug logs by default. Override here.
    ##dssSanityLib.RADOSHOST = '127.0.0.1'                      # The lib points to DSS staging endpoint by default. Override here.
    ##dssSanityLib.RADOSPORT = 7480                             # The lib points to DSS staging endpoint by default. Override here.

    ret = dssSanityLib.fetchArgs(argv)
    if(ret == -1):
        sys.exit(2)

    ## TESTCASES
    dssSanityLib.callTest(bucketSanity(), "Create buckets and objects then delete them")
    dssSanityLib.callTest(multipartObjectUpload(), "Upload object in Multiparts")
    dssSanityLib.callTest(dnsNamesTest(), "Check various DNS name rules")
    dssSanityLib.callTest(publicUrlTest(), "Public URL test")

    ## CLEANUP
    userObj = dssSanityLib.getConnection()
    dssSanityLib.cleanupUser(userObj, 'rjilbucketsanity')
    return

if __name__ == "__main__":
    main(sys.argv[1:])

####################################################
