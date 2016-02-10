#!/bin/python
import sys
import dssSanityLib
from boto.s3.key import Key

################### FUNCTIONS ######################

def listBucket(targ):
    if (dssSanityLib.CLI_USER):
        userObj = dssSanityLib.getConnection(int(dssSanityLib.CLI_USER))
    else:
        userObj = dssSanityLib.getConnection()
    if (not targ):
        dssSanityLib.listBucketNum(userObj, "user")
        dssSanityLib.listBucket(userObj, "user")
    else:
        print "Listing bucket " + str(targ)
        b = userObj.get_bucket(targ)
        for k in b.list():
            print str(k)
    return

def createBucket(num, targ):
    pref = dssSanityLib.getsNewBucketName(targ)
    if (dssSanityLib.CLI_USER):
        userObj = dssSanityLib.getConnection(int(dssSanityLib.CLI_USER))
    else:
        userObj = dssSanityLib.getConnection()

    for i in range(1, int(num) + 1):
        buckname = pref + str(i)
        dssSanityLib.whisper("Creating bucket " + buckname)
        userObj.create_bucket(buckname)
    return

def createObject(num, targ):
    if (dssSanityLib.CLI_USER):
        userObj = dssSanityLib.getConnection(int(dssSanityLib.CLI_USER))
    else:
        userObj = dssSanityLib.getConnection()
    b = userObj.get_bucket(targ)
    k = Key(b)
    for i in range(1, int(num) + 1):
        k.key = 'Obj_' + str(i)
        k.set_contents_from_string("User data for obj")
    return

def deleteBucket(targ):
    if (not targ):
        print "Need target to delete!"
        return -1
    if (dssSanityLib.CLI_USER):
        userObj = dssSanityLib.getConnection(int(dssSanityLib.CLI_USER))
    else:
        userObj = dssSanityLib.getConnection()
    dssSanityLib.cleanupUser(userObj, targ)
    return

###################### MAIN ########################

def main(argv):

    ## PARAM OVERRIDES
    dssSanityLib.GLOBAL_DEBUG = 1             # The lib supresses debug logs by default. Override here.
    ##dssSanityLib.RADOSHOST = '127.0.0.1'      # The lib points to DSS staging endpoint by default. Override here.
    ##dssSanityLib.RADOSPORT = 7480             # The lib points to DSS staging endpoint by default. Override here.

    ret = dssSanityLib.fetchArgs(argv)
    if(ret == -1):
        sys.exit(2)

    if (dssSanityLib.CLI_COMMAND == 'list_bucket'):
        listBucket(dssSanityLib.COMMAND_TARG)
    elif (dssSanityLib.CLI_COMMAND == 'create_bucket'):
        createBucket(dssSanityLib.COMMAND_NUM, dssSanityLib.COMMAND_TARG)
    elif (dssSanityLib.CLI_COMMAND == 'create_object'):
        createObject(dssSanityLib.COMMAND_NUM, dssSanityLib.COMMAND_TARG)
    elif (dssSanityLib.CLI_COMMAND == 'delete_bucket'):
        deleteBucket(dssSanityLib.COMMAND_TARG)
    else:
        print 'cli.py {-a <Access Key> -s <Secret Key>} or {-i True (To read from dsskeys)} -c <command> -n <number> -t <target> -u <user sequence number>'
        print 'cli.py {--access-key <Access Key> --secret-key <Secret Key>} or { --ifile True (To read from dsskeys)} [--command --number --target --user]'
        print "\nList of commands:"
        print "list_bucket {--target <bucket-name>}  :  List all buckets or objects of a single bucket."
        print "create_bucket [--number <number of buckets>] [--target <bucket-name-prefix>]  :  Create some buckets."
        print "create_object [--number <number of objects>] [--target <existing-bucket-name>]  :  Create some objects in an existing bucket."
        print "delete_bucket [--target <bucket-pref>]  :  Deletes all buckets and objects with this name prefix. buck12 will also delete buck123."

    return

if __name__ == "__main__":
    main(sys.argv[1:])

####################################################
