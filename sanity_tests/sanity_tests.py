import os
import sys
import time
import math
import dssSanityLib
import json
import subprocess
from boto.s3.key import Key
from random import randint
from filechunkio import FileChunkIO

############### MAX BUCKET LIMIT ###################

def bucketSanity():

    ## Create five buckets
    dssSanityLib.whisper("Creating buckets and putting objects in them...")
    bucketpref = dssSanityLib.getsNewBucketName()
    dssSanityLib.createMaxBuckets(12, bucketpref,1)

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
def crossAccountSanity():
    x=randint(0,1000)
    buckName='buck'+str(x)
    userObj = dssSanityLib.getConnection(1)
    userObj2 = dssSanityLib.getConnection(2)
    userObj.create_bucket(buckName)
    try:
        userObj2.delete_bucket(buckName)
    except:
        print "Expected failure as permissions are not yet given to User2"
        print "Expected error: ", sys.exc_info()

    os.system("cd jcsclient")
    #os.system("source openrc_raj1_Staging")
    dssSanityLib.sourceCLI(1)

    try:
        command = dssSanityLib.getCreateResourcePolicyCommand(2,x)
        ret = os.popen(command).read()
        print ret
        pairs=ret.split(",")
        #print pairs[3]
        values=pairs[2].split("\"")
        print values[3]
        policyId=values[3]
        command = dssSanityLib.getAttachPolicyToResourceCommand(1,buckName,policyId)
        ret = os.popen(command).read()
    except:
        print "Unexpected error in creating a policy and attaching resource to it"
        return -1
    dssSanityLib.sourceCLI(2)
    command = dssSanityLib.getCreateUserPolicyCommand(1,x, buckName)
    ret = os.popen(command).read()
    print ret
    pairs=ret.split(",")
        #print pairs[3]
    values=pairs[2].split("\"")
    print values[3]
    policyId1=values[3]
    command = dssSanityLib.getAttachPolicyToUserCommand(2,policyId1)


    print "executed command is:: "+command
    ret = os.popen(command).read()

    try:
        userObj2.delete_bucket(buckName)
    except:
        print "Not able to delete bucket despite giving permissions"
        return -1
        print ret

    try:
        print "cleaning up"
        command="jcs iam DeletePolicy --Id "+policyId1
        print "executed command is:: "+command
        ret = os.popen(command).read()
        print ret
        dssSanityLib.sourceCLI(1)
        command="jcs iam DeleteResourceBasedPolicy --Id "+policyId
        print "executed command is:: "+command
        ret = os.popen(command).read()
        print ret
    except:
        print "Error in deleting the resourceBasedPolicy"
        return -1

    bucks=userObj.get_all_buckets()
    for bucket in bucks:
        print "Checking for "+bucket.name
        #userObj.delete_bucket(bucket.name)
        if (bucket.name == buckName):
            print "Bucket still present despite being deleted by the second account"
            return -1


    os.system("cd ..")

    return 0


def crossAccountInSanity():
    x=randint(0,1000)
    # specify the bucket name of the third account
    buckName='buck264'
    userObj = dssSanityLib.getConnection(1)
    userObj2 = dssSanityLib.getConnection(2)
    #userObj.create_bucket(buckName)
    try:
        b=userObj2.get_bucket(buckName)
    except:
        print "Expected failure as permissions are not yet given to User2"
        print "Expected error: ", sys.exc_info()

    os.system("cd jcsclient")
    #os.system("source openrc_raj1_Staging")
    dssSanityLib.sourceCLI(1)

    try:
        command ="jcs iam CreateResourceBasedPolicy --PolicyDocument \"{\\\"name\\\": \\\"DeleteBucket"+str(x)+"\\\", \\\"statement\\\": [{\\\"action\\\": [\\\"jrn:jcs:dss:ListBucket\\\"], \\\"principle\\\": [\\\"jrn:jcs:iam:713268835218:User:rajat\\\"], \\\"effect\\\": \\\"allow\\\"}]}\""
        print "executed command is:: "+command
        ret = os.popen(command).read()
        print ret
        pairs=ret.split(",")
        #print pairs[3]
        values=pairs[2].split("\"")
        print values[3]
        policyId=values[3]
        command="jcs iam AttachPolicyToResource --PolicyId "+policyId+" --Resource \"{\\\"resource\\\": [\\\"jrn:jcs:dss:319505121107:Bucket:"+buckName+"\\\"]}\""
        print "executed command is:: "+command
        ret = os.popen(command).read()
    except:
        print "Unexpected error in creating a policy and attaching resource to it"
        return -1
    #userObj = dssSanityLib.getConnection(2)
    try:
        b=userObj2.get_bucket(buckName)
    except:
        print "Not able to get bucket despite giving permissions"
        return -1
        print ret

    try:
        command="jcs iam DeleteResourceBasedPolicy --Id "+policyId
        print "executed command is:: "+command
        ret = os.popen(command).read()
        print ret
    except:
        print "Error in deleting the resourceBasedPolicy"
        return -1

    bucks=userObj.get_all_buckets()
    for bucket in bucks:
        print "Checking for "+bucket.name
        #userObj.delete_bucket(bucket.name)
        if (bucket.name == buckName):
            print "Bucket still present despite being deleted by the second account"


    os.system("cd ..")

    return 0

def multipartObjectUpload():
    result = 0
    dssSanityLib.whisper("Making bucket and listing...")
    userObj = dssSanityLib.getConnection()
    bucketpref = dssSanityLib.getsNewBucketName()
    b = userObj.create_bucket(bucketpref)
    b.set_acl('public-read-write')
    dssSanityLib.listBucket(userObj, "User")

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
    longHundredChars = 'a123456789a123456789a123456789a123456789a123456789a123456789a123456789a123456789a123456789a123456789'
    longFiftyChars = 'a123456789a123456789a123456789a123456789a123456789'
    longTFTchars = longHundredChars + longHundredChars + longFiftyChars + 'qwe'
    try:
        userObj.create_bucket(longTFTchars)
        userObj.delete_bucket(longTFTchars)
        print "Able to create bucket with 253 chars in name"
    except:
        print "Failed to create or delete a valid bucket name"
        print "Unexpected error: ", sys.exc_info()
        return -1

    try:
        badName = longTFTchars + 'abc'
        userObj.create_bucket(badName)
        print "Unexpectedly created bucket with illegally long name"
        dssSanityLib.listBucketNum(userObj, "user")
        dssSanityLib.listBucket(userObj, "user")
        userObj.delete_bucket(badName)
        result = -1
    except:
        print "Expected failure in creating 256 char bucket name"
        print "Expected error: ", sys.exc_info()

    try:
        badName = 'Abc'
        userObj.create_bucket(badName)
        print "Unexpectedly created bucket with capital letter name"
        dssSanityLib.listBucketNum(userObj, "user")
        dssSanityLib.listBucket(userObj, "user")
        userObj.delete_bucket(badName)
        result = -1
    except:
        print "Expected failure in creating bucket name with CAPS"
        print "Expected error: ", sys.exc_info()

    try:
        badName = 'bc/'
        userObj.create_bucket(badName)
        print "Unexpectedly created bucket with slash in name"
        dssSanityLib.listBucketNum(userObj, "user")
        dssSanityLib.listBucket(userObj, "user")
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
    print "Setting ACL on bucket"
    b1.set_acl('public-read')

    k = Key(b1)
    k.key = 'userObj1'
    k.set_contents_from_string('Data of URL object')
    print "Setting ACL on obj"
    k.set_acl('public-read')

    m = Key(b1)
    m.key = 'userObj1'
    urlname = m.generate_url(1000)
    print "\nThe userObj URL is: " + str(urlname)
    urlname = b1.generate_url(1000)
    print "\nThe bucket URL is: " + str(urlname)

    for i in range(1, 21):
        time.sleep(1)
        if i % 5 == 0:
            print str(20 - i) + " Seconds left before Obj deletion"
    m.delete()
    print "Object deleted\n"

    for i in range(1, 21):
        time.sleep(1)
        if i % 5 == 0:
            print str(20 - i) + " Seconds left before bucket deletion"
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
    dssSanityLib.callTest(crossAccountSanity(), "Giving Delete bucket permission to other account and removing policies")
    #dssSanityLib.callTest(crossAccountInSanity(), "Giving Delete bucket permission to another account on a resource owned by a third account ")

    ## CLEANUP
    userObj = dssSanityLib.getConnection()
    dssSanityLib.cleanupUser(userObj, 'rjilbucketsanity')
    return

if __name__ == "__main__":
    main(sys.argv[1:])

####################################################
