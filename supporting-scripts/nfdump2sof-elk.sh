#!/bin/bash
# SOF-ELK® Supporting script
# (C)2025 Lewes Technology Consulting, LLC
#
# This script will read a file or directory tree of nfcapd-compatible netflow
#   data and output in a format that SOF-ELK® can read with its NetFlow ingest
#   feature

functions_include="/usr/local/sof-elk/supporting-scripts/functions.sh"
if [ -f ${functions_include} ]; then
    . ${functions_include}
else
    echo "${functions_include} not present.  Exiting " 1>&2
    exit 1
fi

# set default values
NONSTANDARD_OUTPUT=0

# parse options
while getopts ":e:r:w:" opt; do
  case "${opt}" in
    e) EXPORTER_IP="${OPTARG}" ;;
    r) SOURCE_LOCATION="${OPTARG}" ;;
    w) DESTINATION_FILE="${OPTARG}" ;;
    \?)
        echoerr "ERROR: Invalid option: -${OPTARG}."
        exit 2
        ;;
  esac
done

if [[ -z ${SOURCE_LOCATION} ]]; then
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
if ! which nfdump > /dev/null; then
    echoerr "ERROR: nfdump not found - exiting."
    exit 3
fi

if [ -d "${SOURCE_LOCATION}" ]; then
    MODE="dir"
elif [ -f "${SOURCE_LOCATION}" ]; then
    MODE="file"
else
    echoerr "ERROR: Invalid source location specified.  Exiting."
    exit 4
fi

if [ "${MODE}" == "dir" ]; then
    READFLAG="-R"
elif [ "${MODE}" == "file" ]; then
    READFLAG="-r"
fi

# validate output file location
if [ -z "${DESTINATION_FILE}" ]; then
    echoerr "ERROR: No destination file specified.  Exiting."
    exit 8
fi

if [ -d "$( dirname "${DESTINATION_FILE}" )" ]; then
    DESTINATION_FILE=$( realpath "${DESTINATION_FILE}" )
else
    echoerr "ERROR: Parent path to requested destination file does not exist.  Exiting."
    exit 9
fi

if [[ ! "${DESTINATION_FILE}" =~ ^/logstash/nfarch/ ]]; then
    echoerr "WARNING: Output file location is not in /logstash/nfarch/. Resulting file will"
    echoerr "         not be automatically ingested unless moved/copied to the correct"
    echoerr "         filesystem location."
    echoerr "         Press Ctrl-C to try again or <Enter> to continue."
    read -r
    NONSTANDARD_OUTPUT=1
fi

# validate source data location
nfdump "${READFLAG}" "${SOURCE_LOCATION}" -q -c 1 > /dev/null 2>&1

TEST_RUN=$?
if [ ${TEST_RUN} != 0 ]; then
    echoerr "ERROR: Source data problem - please address prior to running this command."
    exit 5
fi

# validate exporter IP address
if [[ -z "${EXPORTER_IP}" ]]; then
    echoerr "WARNING: Using default exporter IP address. Specify with '-e' if needed."
    echoerr "         Press Ctrl-C to try again or <Enter> to continue."
    read -r
    EXPORTER_IP="0.0.0.0"
fi
if ! is_valid_ip "${EXPORTER_IP}"; then
    echoerr "ERROR: Invalid Exporter IP address provided - exiting."
    exit 6
fi

# finally run nfdump command
echoerr "Running distillation.  Putting output in ${DESTINATION_FILE}"
nfdump "${READFLAG}" "${SOURCE_LOCATION}" -6 -q -N -o "fmt:${EXPORTER_IP} ${NFDUMP2SOFELK_FMT}" > "${DESTINATION_FILE}"

REAL_RUN=$?
if [ ${REAL_RUN} != 0 ]; then
    echoerr "ERROR: An unknown error occurred - data may not have loaded correctly."
    exit 7
else
    echoerr "Text file creation complete."
    if [ ${NONSTANDARD_OUTPUT} ]; then
        echoerr "You must move/copy the generated file to the /logstash/nfarch/ directory before"
        echoerr "  SOF-ELK can process it."
    else
        echoerr "SOF-ELK should now be processing the generated file - check system load and the"
        echoerr "  Kibana interface to confirm."
    fi
fi
