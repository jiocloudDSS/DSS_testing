import os
import sys
import time
import dssSanityLib
from boto.s3.key import Key

###################### MAIN ########################

def main(argv):

    ## PARAM OVERRIDES
    dssSanityLib.GLOBAL_DEBUG = 1                    # The lib supresses debug logs by default. Override here.
    #dssSanityLib.RADOSHOST = '127.0.0.1'             # The lib points to DSS staging endpoint by default. Override here.
    #dssSanityLib.RADOSPORT = 7480                    # The lib points to DSS staging endpoint by default. Override here.

    ret = dssSanityLib.fetchArgs(argv)
    if(ret == -1):
        sys.exit(2)

    userObj = dssSanityLib.getConnection()

#    userObj.create_bucket('bucket0');
#    userObj.create_bucket('bucket1');
#    userObj.create_bucket('bucket2');
#    userObj.create_bucket('bucket3');
#    userObj.create_bucket('bucket4');
#    userObj.create_bucket('bucket5');
#    userObj.create_bucket('bucket6');
#    userObj.create_bucket('bucket7');
#    userObj.create_bucket('bucket8');
#    userObj.create_bucket('bucket9');
    print userObj.get_all_buckets()
    return

if __name__ == "__main__":
    main(sys.argv[1:])

####################################################
