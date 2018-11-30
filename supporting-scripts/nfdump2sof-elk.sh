#!/bin/bash
# SOF-ELK® Supporting script
# (C)2018 Lewes Technology Consulting, LLC
#
# This script will read a file or directory tree of nfcapd-compatible netflow data and output in a format that SOF-ELK® can read with its NetFlow ingest feature

# bash functionality to get command-line parameters
# source: http://stackoverflow.com/questions/192249/how-do-i-parse-command-line-arguments-in-bash
# Use -gt 1 to consume two arguments per pass in the loop (e.g. each
# argument has a corresponding value to go with it).
# Use -gt 0 to consume one or more arguments per pass in the loop (e.g.
# some arguments don't have a corresponding value to go with it such
# as in the --default example).

# bash function to validate IP (v4) addresses
# source: http://www.linuxjournal.com/content/validating-ip-address-bash-script
valid_ip() {
    local  ip=$1
    local  stat=1

    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        OIFS=$IFS
        IFS='.'
        ip=($ip)
        IFS=$OIFS
        [[ ${ip[0]} -le 255 && ${ip[1]} -le 255 && ${ip[2]} -le 255 && ${ip[3]} -le 255 ]]
        stat=$?
    fi
    return $stat
}

# bash function to echo to STDERR instead of STDOUT
# source: https://stackoverflow.com/a/2990533/1400064
echoerr() { echo "$@" 1>&2; }

while [[ $# -gt 1 ]]; do
    key="$1"

    case $key in
        -e|--exporter)
        EXPORTER_IP="$2"
        shift # past argument
        ;;
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
    echoerr "Please supply a source nfcapd filename or parent directory containing nfcapd data"
    echoerr "   to be parsed for SOF-ELK."
    echoerr ""
    echoerr "Example: $0 -r /path/to/netflow/nfcapd.201703190000 -w /logstash/nfarch/<filename>.txt"
    echoerr "Example: $0 -r /path/to/netflow/ -w /logstash/nfarch/<filename>.txt"
    echoerr ""
    echoerr "Can optionally supply an exporter IP address"
    echoerr
    echoerr "Example: $0 -e 1.2.3.4 -r /path/to/netflow/ -w /logstash/nfarch/<filename>.txt"
    echoerr ""
    exit 2
fi

# this is the custom format that SOF-ELK® will understand
NFDUMP2SOFELK_FMT="%das %dmk %eng %ts %fl 0 %byt %pkt %in %da %nh %sa %dp %sp %te %out %pr 0 0 %sas %smk %stos %flg 0"

# make sure nfdump is available
if [ ! $( which nfdump ) ]; then
    echoerr "ERROR: nfdump not found - exiting."
    exit 3
fi

if [ -d $SOURCE_LOCATION ]; then
    MODE="dir"
elif [ -f $SOURCE_LOCATION ]; then
    MODE="file"
else
    echoerr "ERROR: Invalid source location specified.  Exiting."
    exit 4
fi

if [ $MODE == "dir" ]; then
    READFLAG="-R"
elif [ $MODE == "file" ]; then
    READFLAG="-r"
fi

# validate output file location
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

# validate source data location
nfdump $READFLAG $SOURCE_LOCATION -q -c 1 > /dev/null 2>&1

TEST_RUN=$?
if [ $TEST_RUN != 0 ]; then
    echoerr ""
    echoerr "ERROR: Source data problem - please address prior to running this command."
    exit 5
fi

# validate exporter IP address
if [[ $EXPORTER_IP == "" ]]; then
    echoerr "WARNING: Using default exporter IP address. Specify with '-e' if needed."
    echoerr "         Press Ctrl-C to try again or <Enter> to continue."
    read
    EXPORTER_IP="0.0.0.0"
fi

if ! valid_ip $EXPORTER_IP; then
    echoerr ""
    echoerr "ERROR: Invalid Exporter IP address provided - exiting."
    exit 6
fi

# finally run nfdump command
echoerr "Running distillation.  Putting output in $DESTINATION_FILE"
nfdump $READFLAG $SOURCE_LOCATION -q -N -o "fmt:$EXPORTER_IP $NFDUMP2SOFELK_FMT" > $DESTINATION_FILE

REAL_RUN=$?
if [ $REAL_RUN != 0 ]; then
    echoerr ""
    echoerr "ERROR: An unknown error occurred - data may not have loaded correctly."
    exit 7
else
    echoerr ""
    echoerr "Text file creation complete."
    if [ $NONSTANDARD_OUTPUT ]; then
        echoerr "You must move/copy the generated file to the /logstash/nfarch/ directory before"
        echoerr "  SOF-ELK can process it."
    else
        echoerr "SOF-ELK should now be processing the generated file - check system load and the"
        echoerr "  Kibana interface to confirm."
    fi
fi