#!/bin/bash
# SOF-ELK® Supporting script
# (C)2024 Lewes Technology Consulting, LLC
#
# This script will read a file or directory tree of nfcapd-compatible netflow data and output in a format that SOF-ELK® can read with its NetFlow ingest feature

# bash functionality to get command-line parameters
# source: http://stackoverflow.com/questions/192249/how-do-i-parse-command-line-arguments-in-bash
# Use -gt 1 to consume two arguments per pass in the loop (e.g. each
# argument has a corresponding value to go with it).
# Use -gt 0 to consume one or more arguments per pass in the loop (e.g.
# some arguments don't have a corresponding value to go with it such
# as in the --default example).
while [[ $# -gt 1 ]]; do
    key="$1"

    case $key in
        -a|--action)
        ACTION="$2"
        shift # past argument
        ;;
        -p|--port)
        PORT="$2"
        shift # past argument
        ;;
        -r|--protocol)
        PROTOCOL="$2"
        shift # past argument
        ;;
        *)
        # unknown option
        ;;
    esac
    shift # past argument or value
done

if [[ -z "${ACTION}" || ( "${ACTION}" != "open" && "${ACTION}" != "close" ) ]]; then
    echo
    echo "Please specify the firewall action to take with the '-a' option.  Options are 'open' or 'closed'."
    echo
    echo "Example: $0 -a open -p 5514 -r tcp"
    echo
    exit 2
fi

if [[ -z "${PORT}" ]]; then
    echo
    echo "Please specify the port to act on with the '-p' option."
    echo
    echo "Example: $0 -a open -p 5514 -r tcp"
    echo
    exit 3
fi

re='^[0-9]+$'
if ! [[ "${PORT}" =~ ${re} ]] ; then
    echo
    echo "Error - ${PORT} is not a number.  Exiting."
    echo
    exit 4
fi

if [[ -z "${PROTOCOL}" || ( "${PROTOCOL}" != "tcp" && "${PROTOCOL}" != "udp" ) ]]; then
    echo
    echo "Please specify the protocol to act on with the '-r' option.  Options are 'tcp' or 'udp'."
    echo
    echo "Example: $0 -a open -p 5514 -r tcp"
    echo
    exit 2
fi

firewall-cmd --zone=public --add-port="${PORT}"/"${PROTOCOL}" --permanent
firewall-cmd --reload
