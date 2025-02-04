#!/bin/bash
# SOF-ELK® Supporting script
# (C)2024 Lewes Technology Consulting, LLC
#
# This script will read a file or directory tree of JSON VPC Flow logs and
# output in a format that SOF-ELK® can read with its NetFlow ingest feature

# bash function to echo to STDERR instead of STDOUT
# source: https://stackoverflow.com/a/2990533/1400064
echoerr() {
  echo "$@" 1>&2;
}

while getopts ":r:w:" opt; do
  case "${opt}" in
    r) SOURCE_LOCATION="${OPTARG}" ;;
    w) DESTINATION_FILE="${OPTARG}" ;;
    :)
      echoerr "ERROR: -${OPTARG} requires an argument."
      exit 1
      ;;
    ?)
      echoerr "ERROR: Invalid option: -${OPTARG}."
      exit 2
      ;;
  esac
done

if [[ -z "${SOURCE_LOCATION}" ]]; then
  echoerr ""
  echoerr "Please supply a source filename or parent directory containing VPC Flow"
  echoerr "  data to be parsed for SOF-ELK."
  echoerr ""
  echoerr "Example:"
  echoerr "  $0 -r /path/to/vpcflow/dm-flowlogs.json -w /logstash/nfarch/<filename>.txt"
  echoerr "Example:"
  echoerr "  $0 -r /path/to/vpcflow/ -w /logstash/nfarch/<filename>.txt"
  echoerr ""
  exit 3
fi

# make sure jq is available
if ! which jq ; then
  echoerr "jq not found - exiting."
  exit 4
fi
# make sure realpath is available
if ! which realpath ; then
  echoerr "realpath not found - exiting."
  exit 5
fi

if [ ! -d "${SOURCE_LOCATION}" ] && [ ! -f "${SOURCE_LOCATION}" ]; then
  echoerr "Invalid source location specified.  Exiting."
  exit 6
fi

if [ -d "$( dirname "${DESTINATION_FILE}" )" ]; then
  DESTINATION_FILE=$( realpath "${DESTINATION_FILE}" )
else
  echoerr "ERROR: Parent path to requested destination file does not exist.  Exiting."
  exit 7
fi

if [[ ! "${DESTINATION_FILE}" =~ ^/logstash/nfarch/ ]]; then
  echoerr "WARNING: Output file location is not in /logstash/nfarch/. Resulting file will"
  echoerr "         not be automatically ingested unless moved/copied to the correct"
  echoerr "         filesystem location."
  echoerr "         Press Ctrl-C to try again or <Enter> to continue."
  read -r
  NONSTANDARD_OUTPUT=1
fi

# prepare list of input file(s) to read
# TODO: this doesn't handle spaces in directory/file names
IFS="
"
READFILES=$( find "${SOURCE_LOCATION}" -type f -print )

CONVERT_SUCCESS=0
for READFILE in ${READFILES}; do
  # validate source data location
  jq -crM '.events[1].message' < "${READFILE}" 2> /dev/null

  TEST_RUN=$?
  if [ ${TEST_RUN} != 0 ]; then
    echoerr ""
    echoerr "Error with source file ${READFILE} - skipping."
    continue
  fi

  # finally run jq command
  jq -crM '.events[].message' < "${READFILE}" > "${DESTINATION_FILE}"

  REAL_RUN=$?
  if [ "${REAL_RUN}" != 0 ]; then
    echoerr ""
    echoerr "An error occurred with source file ${READFILE}."
    echoerr "Data may not have loaded correctly."
    continue
  else
    CONVERT_SUCCESS=1
  fi
done

echoerr ""
if [ "${CONVERT_SUCCESS}" == 1 ]; then
  echoerr "Output complete."
  if [ "${NONSTANDARD_OUTPUT}" ]; then
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
