#!/bin/bash

# cat h.json | jq '.Records[] | select((.resources == null) or (any(.resources[].ARN; contains ("arn:aws:s3:::for509trails")) | not))' | jq -n '.Records |= [inputs]'

# This script will read a file or directory tree of JSON Cloudtrail logs and create a parallel structure after filtering out specified records.

# bash functionality to get command-line parameters
# source: http://stackoverflow.com/questions/192249/how-do-i-parse-command-line-arguments-in-bash
# Use -gt 1 to consume two arguments per pass in the loop (e.g. each argument has a corresponding value to go with it).
# Use -gt 0 to consume one or more arguments per pass in the loop (e.g. some arguments don't have a corresponding value to go with it such as in the --default example).
while [[ $# -gt 1 ]]; do
    key="$1"

    case $key in
        -r|--sourcelocation)
        SOURCE_LOCATION="$2"
        shift # past argument
        ;;
        -w|--destlocation)
        DESTINATION_LOCATION="$2"
        shift # past argument
        ;;
        *)
        # unknown option
        ;;
    esac
    shift # past argument or value
done

# bash function to echo to STDERR instead of STDOUT
# source: https://stackoverflow.com/a/2990533/1400064
echoerr() { echo "$@" 1>&2; }

# make sure jq is available
if [ ! $( which jq ) ]; then
    echoerr "jq not found - exiting."
    exit 1
fi
# make sure realpath is available
if [ ! $( which realpath ) ]; then
    echoerr "realpath not found - exiting."
    exit 1
fi

if [[ $SOURCE_LOCATION == "" ]]; then
    echoerr ""
    echoerr "Please supply a source directory containing the Cloudtrail logs to be reduced."
    echoerr ""
    echoerr "Example: $0 -r /path/to/cloudtrail_logs/ -w ~/reduced_cloudtrail_logs/"
    echoerr ""
    exit 2
fi

if [ ! -d "$SOURCE_LOCATION" -a ! -f "$SOURCE_LOCATION" ]; then
    echoerr "Invalid source location specified.  Exiting."
    exit 3
fi

if [ -z $DESTINATION_LOCATION ]; then
    echoerr "ERROR: No destination location specified.  Exiting."
    exit 4
fi

if [ -d $( dirname $DESTINATION_LOCATION ) ]; then
    DESTINATION_LOCATION=$( realpath $DESTINATION_LOCATION )

else
    echoerr "ERROR: Parent path to requested destination location does not exist.  Exiting."
    exit 5
fi

OLDIFS=$IFS
IFS="
"
READFILES=$( find $SOURCE_LOCATION -type f -print )

for READFILE in $READFILES; do
    COMPRESSED_FILE=0
    if ( file $READFILE | grep -q gzip ); then
        COMPRESSED_FILE=1
    fi

    DIRNAME=$( dirname $READFILE )
    FILENAME=$( basename $READFILE )
    DIR_STRUCTURE=${DIRNAME#$SOURCE_LOCATION}

    # validate source data location
    if [ $COMPRESSED_FILE == 0 ]; then
        cat $READFILE | jq -crM '.Records[0].eventName' > /dev/null 2>&1
    elif [ $COMPRESSED_FILE == 1 ]; then
        gunzip -c $READFILE | jq -crM '.Records[0].eventName' > /dev/null 2>&1
    fi

    TEST_RUN=$?
    if [ $TEST_RUN != 0 ]; then
        echoerr ""
        echoerr "Error with source file ${READFILE} - skipping."
        continue
    fi

    # finally run jq commands
    echo "processing $READFILE"
    if [ ! -d $DESTINATION_LOCATION/$DIR_STRUCTURE ]; then
       mkdir -p $DESTINATION_LOCATION/$DIR_STRUCTURE
    fi
    if [ $COMPRESSED_FILE == 0 ]; then
        cat $READFILE | jq '.Records[] | select(.requestParameters.bucketName == null or .requestParameters.bucketName != "for509trails")' | jq -cn '.Records |= [inputs]' > $DESTINATION_LOCATION/$DIR_STRUCTURE/$FILENAME
    elif [ $COMPRESSED_FILE == 1 ]; then
        gunzip -c $READFILE | jq '.Records[] | select(.requestParameters.bucketName == null or .requestParameters.bucketName != "for509trails")' | jq -cn '.Records |= [inputs]' | gzip -f > $DESTINATION_LOCATION/$DIR_STRUCTURE/$FILENAME
    fi
done
