import re
import os
import sys
import time
import boto
import getopt
import sys
from boto.s3.key import Key
from boto.s3.connection import S3Connection

###################### INIT ########################

# PARAMS
GLOBAL_DEBUG = 0
MULTIPART_LARGE_FILE = ''
RADOSHOST    = 'dss.ind-west-1.staging.jiocloudservices.com'
#RADOSHOST    = '10.140.214.196'
#RADOSPORT    = '7480' 
RADOSPORT    = '' 
CLI_USER     = ''
CLI_COMMAND  = ''
COMMAND_NUM  = ''
COMMAND_TARG = ''

# ACCESS PARAMS
access_key = ''
secret_key = ''
user_profiles = None
isSecure   = True
#isSecure   = False
isAwsConn  = False
has_incore_params = False

####################################################

################## CREATE CONNECTION ###############
def sourceCLI(user = None):
    global user_profiles
    if (user is not None) and (user_profiles is not None):
        try:
            access_key = user_profiles[user]['access']
            secret_key = user_profiles[user]['secret']
            #os.system("export DSS_URL=https://dss.ind-west-1.jiocloudservices.com")
            #os.system("export ACCESS_KEY=access_key")
            #os.system("export SECRET_KEY=secret_key")
            os.environ['IAM_URL']='https://iam.ind-west-1.staging.jiocloudservices.com'
            os.environ['DSS_URL']='https://dss.ind-west-1.staging.jiocloudservices.com'
            os.environ['ACCESS_KEY'] = access_key
            os.environ['SECRET_KEY'] = secret_key
        except:
            print "Must have dsskeys file for multiuser access!"
            return -1

def getCreateResourcePolicyCommand(user = None, x=None):
    global user_profiles
    if (user is not None) and (user_profiles is not None):
        try:
            account_id = user_profiles[user]['account_id']
            user_name = user_profiles[user]['name']
            command ="jcs iam CreateResourceBasedPolicy --PolicyDocument \"{\\\"name\\\": \\\"DeleteBucket"+str(x)+"\\\", \\\"statement\\\": [{\\\"action\\\": [\\\"jrn:jcs:dss:DeleteBucket\\\"], \\\"principle\\\": [\\\"jrn:jcs:iam:"+account_id+":User:"+user_name+"\\\"], \\\"effect\\\": \\\"allow\\\"}]}\""
        except:
            print "Must have dsskeys file for multiuser access!"
            return -1
    print command
    return command

def getAttachPolicyToResourceCommand(user = None, buckName = None, policyId=None):
    global user_profiles
    if (user is not None) and (user_profiles is not None):
        try:
            account_id = user_profiles[user]['account_id']
            command="jcs iam AttachPolicyToResource --PolicyId "+policyId+" --Resource \"{\\\"resource\\\": [\\\"jrn:jcs:dss:"+account_id+":Bucket:"+buckName+"\\\"]}\""
        except:
            print "Must have dsskeys file for multiuser access!"
            return -1
    print command
    return command

def getCreateUserPolicyCommand(user = None, x = None, buckName = None):
    global user_profiles
    if (user is not None) and (user_profiles is not None):
        try:
            account_id = user_profiles[user]['account_id']
            user_name = user_profiles[user]['name']
            command="jcs iam CreatePolicy --PolicyDocument \"{\\\"name\\\": \\\"DeleteBucket1"+str(x)+"\\\", \\\"statement\\\": [{\\\"action\\\": [\\\"jrn:jcs:dss:DeleteBucket\\\"], \\\"resource\\\": [\\\"jrn:jcs:dss:"+account_id+":Bucket:"+buckName+"\\\"], \\\"effect\\\": \\\"allow\\\"}]}\""
        except:
            print "Must have dsskeys file for multiuser access!"
            return -1
    print command
    return command

def getAttachPolicyToUserCommand(user = None, policyId=None):
    global user_profiles
    if (user is not None) and (user_profiles is not None):
        try:
            account_id = user_profiles[user]['account_id']
            command="jcs iam AttachPolicyToUser --PolicyId "+policyId+" --UserId "+account_id
        except:
            print "Must have dsskeys file for multiuser access!"
            return -1
    print command
    return command

def getConnection(user = None):
    global has_incore_params
    global access_key
    global secret_key
    global user_profiles

    if (user is not None) and (user_profiles is not None):
        try:
            access_key = user_profiles[user]['access']
            secret_key = user_profiles[user]['secret']
        except:
            print "Must have dsskeys file for multiuser access!"
            return -1

    conn_obj = None
    if (has_incore_params and (GLOBAL_DEBUG == 1)):
        conn_obj = boto.connect_s3(
            aws_access_key_id     = access_key,
            aws_secret_access_key = secret_key,
            host = RADOSHOST,
            port = RADOSPORT,
            is_secure = isSecure,
            calling_format = boto.s3.connection.OrdinaryCallingFormat(),
            debug = 2,
        )
    elif (has_incore_params and (GLOBAL_DEBUG == 0)):
        conn_obj = boto.connect_s3(
            aws_access_key_id     = access_key,
            aws_secret_access_key = secret_key,
            host = RADOSHOST,
            port = RADOSPORT,
            is_secure = isSecure,
            calling_format = boto.s3.connection.OrdinaryCallingFormat(),
        )
    elif (has_incore_params and isAwsConn):
        conn_obj = S3Connection(access_key, secret_key)
    else:
        return -1
    return conn_obj

####################################################

############### INFO PRESENTATION ##################

def whisper(mystr):
    if GLOBAL_DEBUG == 1:
        print "DEBUG: " + mystr
    return

def callTest(output, testname):
    if output != 0:
        print "\n\t=====================================\n\t" + testname + " : Failed"
    else:
        print "\n\t=====================================\n\t" + testname + " : Pass"
    print "\t=====================================\n\n"
    return

####################################################

############### DATA POPULATION ####################

def createMaxBuckets(num, buckpref, user = None):
    obj = getConnection(user)
    listBucketNum(obj, "User")
    whisper("Creating new buckets")
    for i in range(1, num + 1):
        name = buckpref + str(i)
        buck = obj.create_bucket(name)
        whisper("Creating bucket " + name)
        for j in range(1, 11):
            k = Key(buck)
            k.key = name + '_OBJ_' + str(j)
            whisper("Creating object " + k.key)
            k.set_contents_from_string('Data for obj ' + str(j))
    return;

####################################################

############## CLEANUP AND LISTING #################

def cleanupUser(userObj, patstr = None):
    whisper("Cleaning up...")
    if (patstr):
        pstring = patstr + '*'
    else:
        pstring = '*'
    pattern = re.compile(pstring)
    for bkt in userObj.get_all_buckets():
        if (pattern.match(bkt.name)) or (not patstr):
            for k in bkt.list():
                whisper("Deleting " + str(k))
                k.delete()
            whisper("Deleting bucket " + str(bkt))
            userObj.delete_bucket(bkt.name)

    listBucket(userObj, "User")
    return

def listBucketNum(userObj, uname):
    print "Total number of buckets for " + uname + ": " + str(len(userObj.get_all_buckets()))
    return

def listBucket(userObj, uname):
    print "Listing buckets for " + uname
    for bucket in userObj.get_all_buckets():
        print "{name}\t{created}".format(name = bucket.name, created = bucket.creation_date)
    return
####################################################

############## KEEP CHANGING ACLS ##################

def keepChangingAcls(bucket):
    obj = getConnection()
    acl_list = ('public-read', 'private')
    for i in range(1, 11):
        b1 = obj.get_bucket(bucket)
        whisper("Changing ACL to " + str(acl_list[i % 2]))
        b1.set_acl(acl_list[i % 2])
        time.sleep(1)
    return
####################################################

################ BUCKET NAME GEN ###################

def getsNewBucketName(pref = None):
    ts = time.time()
    str_ts = str(ts)
    index = str_ts.find('.')
    str_ts = str_ts[0:index]
    if pref is None:
        bucketpref = 'rjilbucketsanity' + str_ts
    else:
        bucketpref = str(pref) + str_ts
    return bucketpref

####################################################

################# CLI ARGUMENTS ####################

def fetchArgs(argv):
    global has_incore_params
    global access_key
    global secret_key
    global user_profiles
    global CLI_USER
    global CLI_COMMAND
    global COMMAND_NUM
    global COMMAND_TARG

    try:
        opts, args = getopt.getopt(argv,"a:s:h:i:c:n:t:u",["access-key=","secret-key=","ifile=","command=","number=","target=","user="])
    except getopt.GetoptError:
        printsHelp()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            printsHelp()
            sys.exit()
        elif opt in ("-c", "--command"):
            CLI_COMMAND = arg
        elif opt in ("-n", "--number"):
            COMMAND_NUM = arg
        elif opt in ("-t", "--target"):
            COMMAND_TARG = arg
        elif opt in ("-u", "--user"):
            CLI_USER = arg
        elif opt in ("-i", "--ifile"):
            try:
                import dsskeys
                has_incore_params = True
                access_key        = dsskeys.access_key
                secret_key        = dsskeys.secret_key
                user_profiles     = dsskeys.user_profiles
            except ImportError:
                print "Error: Failed to import dsskeys from file. Make sure that the file is present."
        elif opt in ("-a", "--access-key"):
            has_incore_params = True
            access_key = arg
        elif opt in ("-s", "--secret-key"):
            print "Sending secret key using command line is unsafe. Use dsskeys file."
            print "Sleeping for 5 seconds before continuing..."
            time.sleep(5)
            secret_key = arg

    if (not has_incore_params):
        printsHelp()
        return -1

    return 0

def printsHelp():
    print "HELP"
    print "===="
    print '<Test script> {-a <Access Key> -s <Secret Key>} or {-i True (To read from dsskeys)}'
    print '<Test script> {--access-key <Access Key> --secret-key <Secret Key>} or { --ifile True (To read from dsskeys)}'
    print "\nDSSKEYS FILE"
    print "============"
    print "Make a file called dsskeys.py and put inside it:"
    print "    access_key = \'<value>\'"
    print "    secret_key = \'<value>\'"
    return

####################################################
