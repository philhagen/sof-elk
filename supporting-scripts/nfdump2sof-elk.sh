#!/bin/bash
# SOF-ELK Supporting script
# (C)2017 Lewes Technology Consulting, LLC
#
# This script will read a file or directory tree of nfcapd-compatible netflow data and output in a format that SOF-ELK can read with its NetFlow ingest feature

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
    echoerr "Example: $0 -r /path/to/netflow/nfcapd.201703190000"
    echoerr "Example: $0 -r /path/to/netflow/"
    echoerr ""
    echoerr "Can optionally supply an exporter IP address"
    echoerr
    echoerr "Example: $0 -e 1.2.3.4 -r /path/to/netflow/"
    echoerr ""
    exit 2
fi

if [[ $EXPORTER_IP == "" ]]; then
    echoerr "WARNING: Using default exporter IP address. Specify with '-e' if needed." >&2
    echoerr "         Press Ctrl-C to try again or <Enter> to continue." >&2
    read
    EXPORTER_IP="0.0.0.0"
fi

# this is the custom format that SOF-ELK will understand
NFDUMP2SOFELK_FMT="%das %dmk %eng %ts %fl 0 %byt %pkt %in %da %nh %sa %dp %sp %te %out %pr 0 0 %sas %smk %stos %flg 0"

# make sure nfdump is available
if [ ! $( which nfdump ) ]; then
    echoerr "nfdump not found - exiting."
    exit 3
fi

if [ -d $SOURCE_LOCATION ]; then
    MODE="dir"
elif [ -f $SOURCE_LOCATION ]; then
    MODE="file"
else
    echoerr "Invalid source location specified.  Exiting."
    exit 4
fi
if [ $MODE == "dir" ]; then
    READFLAG="-R"
elif [ $MODE == "file" ]; then
    READFLAG="-r"
fi

# validate source data location
nfdump $READFLAG $SOURCE_LOCATION -q -c 1 > /dev/null 2>&1

TEST_RUN=$?
if [ $TEST_RUN != 0 ]; then
    echoerr ""
    echoerr "Error with source data - please address prior to running this command."
    exit 5
fi

# validate exporter IP address
if ! valid_ip $EXPORTER_IP; then
    echoerr ""
    echoerr "Invalid Exporter IP address provided - exiting."
    exit 6
fi

# finally run nfdump command
nfdump $READFLAG $SOURCE_LOCATION -q -N -O tstart -o "fmt:$EXPORTER_IP $NFDUMP2SOFELK_FMT"