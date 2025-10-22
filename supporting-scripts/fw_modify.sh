#!/bin/bash
# SOF-ELK® Supporting script
# (C)2025 Lewes Technology Consulting, LLC
#
# This script modifies the local firewall using the firewall-cmd utility

# include common functions
functions_include="/usr/local/sof-elk/supporting-scripts/functions.sh"
if [ -f ${functions_include} ]; then
    . ${functions_include}
else
    echo "${functions_include} not present.  Exiting " 1>&2
    exit 2
fi

# set local functions
usage() {
    echo "Usage: $0 [-h] -a (open|close) -p <%PORT_NUMBER%> -r (tcp|udp)"
    exit 3
}

# parse options
while getopts ":a:p:r:h" opt; do
  case "${opt}" in
    a) ACTION=${OPTARG} ;;
    p) PORT=${OPTARG} ;;
    r) PROTOCOL=${OPTARG} ;;
    h) usage ;;
    \?)
        echoerr "ERROR: Invalid option: -${OPTARG}"
        exit 4
        ;;
  esac
done

# quit if not running with admin privs
require_root

# handle missing or empty options
if [[ -z "${ACTION}" || ( "${ACTION}" != "open" && "${ACTION}" != "close" ) ]]; then
    echo "Please specify the firewall action to take with the '-a' option.  Options are 'open' or 'closed'."
    echo
    echo "Example: $0 -a open -p 5514 -r tcp"
    exit 5
fi

if [[ -z "${PORT}" ]]; then
    echo "Please specify the port to act on with the '-p' option."
    echo
    echo "Example: $0 -a open -p 5514 -r tcp"
    exit 6
fi

re='^[0-9]+$'
if ! [[ "${PORT}" =~ ${re} ]] ; then
    echo "Error - ${PORT} is not a number.  Exiting."
    exit 7
fi

if [[ -z "${PROTOCOL}" || ( "${PROTOCOL}" != "tcp" && "${PROTOCOL}" != "udp" ) ]]; then
    echo "Please specify the protocol to act on with the '-r' option.  Options are 'tcp' or 'udp'."
    echo
    echo "Example: $0 -a open -p 5514 -r tcp"
    exit 8
fi

# take the required firewall-cmd action and reload
if [[ ${ACTION} == "open" ]]; then
    FWCMDARG="--add-port"
else
    FWCMDARG="--remove-port"
fi

firewall-cmd --zone=public ${FWCMDARG}="${PORT}"/"${PROTOCOL}" --permanent > /dev/null
firewall-cmd --reload > /dev/null
