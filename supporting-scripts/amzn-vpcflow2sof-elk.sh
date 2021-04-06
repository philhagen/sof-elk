#!/bin/bash
# SOF-ELK® Supporting script
# (C)2018 Lewes Technology Consulting, LLC
#
# This script will read a file or directory tree of JSON VPC Flow logs and output in a format that SOF-ELK® can read with its NetFlow ingest feature

# bash functionality to get command-line parameters
# source: http://stackoverflow.com/questions/192249/how-do-i-parse-command-line-arguments-in-bash
# Use -gt 1 to consume two arguments per pass in the loop (e.g. each argument has a corresponding value to go with it).
# Use -gt 0 to consume one or more arguments per pass in the loop (e.g. some arguments don't have a corresponding value to go with it such as in the --default example).

# bash function to echo to STDERR instead of STDOUT
# source: https://stackoverflow.com/a/2990533/1400064
echoerr() { echo "$@" 1>&2; }

while [[ $# -gt 1 ]]; do
    key="$1"

    case $key in
        -r|--sourcelocation)
        SOURCE_LOCATION="$2"
        shift # past argument
        ;;
        -w|--destfile)
        DESTINATION_FILE="$2"
        shift # past argument
        ;;
        *)
        # unknown option
        ;;
    esac
    shift # past argument or value
done

if [[ $SOURCE_LOCATION == "" ]]; then
    echoerr ""
    echoerr "Please supply a source nfcapd filename or parent directory containing VPC Flow data"
    echoerr "   to be parsed for SOF-ELK."
    echoerr ""
    echoerr "Example: $0 -r /path/to/vpcflow/dm-flowlogs.json -w /logstash/nfarch/<filename>.txt"
    echoerr "Example: $0 -r /path/to/vpcflow/ -w /logstash/nfarch/<filename>.txt"
    echoerr ""
    exit 2
fi

# VPC Flow doesn't have a concept of "exporter" as far as I can tell
EXPORTER_IP="0.0.0.0"

# make sure jq is available
if [ ! $( which jq ) ]; then
    echoerr "jq not found - exiting."
    exit 3
fi

if [ ! -d "$SOURCE_LOCATION" -a ! -f "$SOURCE_LOCATION" ]; then
    echoerr "Invalid source location specified.  Exiting."
    exit 4
fi

if [ -z $DESTINATION_FILE ]; then
    echoerr "ERROR: No destination file specified.  Exiting."
    exit 8
fi

if [ -d $( dirname $DESTINATION_FILE ) ]; then
    DESTINATION_FILE=$( realpath $DESTINATION_FILE )
else
    echoerr "ERROR: Parent path to requested destination file does not exist.  Exiting."
    exit 9
fi

if [[ ! $DESTINATION_FILE =~ ^/logstash/nfarch/ ]]; then
    echoerr "WARNING: Output file location is not in /logstash/nfarch/. Resulting file will"
    echoerr "         not be automatically ingested unless moved/copied to the correct"
    echoerr "         filesystem location."
    echoerr "         Press Ctrl-C to try again or <Enter> to continue."
    read
    NONSTANDARD_OUTPUT=1
fi

# prepare list of input file(s) to read
# TODO: this doesn't handle spaces in directory/file names
OLDIFS=$IFS
IFS="
"
READFILES=$( find $SOURCE_LOCATION -type f -print )

CONVERT_SUCCESS=0
for READFILE in $READFILES; do
    # validate source data location
    cat $READFILE | jq -crM '.events[1].message' 2> /dev/null

    TEST_RUN=$?
    if [ $TEST_RUN != 0 ]; then
        echoerr ""
        echoerr "Error with source file ${READFILE} - skipping."
        continue
    fi

    # finally run jq command
    cat $READFILE | jq -crM '.events[].message' > ${DESTINATION_FILE}

    REAL_RUN=$?
    if [ $REAL_RUN != 0 ]; then
        echoerr ""
        echoerr "An error occurred with source file ${READFILE} - data may not have loaded correctly."
        continue
    else
        CONVERT_SUCCESS=1
    fi
done

echoerr ""
if [ $CONVERT_SUCCESS == 1 ]; then
    echoerr "Output complete."
    if [ $NONSTANDARD_OUTPUT ]; then
        echoerr "You must move/copy the generated file to the /logstash/nfarch/ directory before"
        echoerr "  SOF-ELK can process it."
    else
        echoerr "SOF-ELK should now be processing the generated file - check system load and the"
        echoerr "  Kibana interface to confirm."
    fi
else
    echoerr "No files were successfully converted."
    echoerr "Please validate the input data to ensure it contains proper JSON data."
fi