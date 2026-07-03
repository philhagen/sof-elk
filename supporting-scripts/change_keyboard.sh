#!/bin/bash
# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
# (C)2018 505 Forensics
#
# This script will assist in making temporary and permanent changes to the
# keyboard layout in SOF-ELK to facilitate international keyboards.
# Usage:
# sudo change_keyboard.sh <country_code>

# Keyboard country codes are typically two-letters (IT, DE, JP, etc.)
# The script will error out if an incorrect code is provided.

# include common functions
functions_include="/usr/local/sof-elk/supporting-scripts/functions.sh"
if [ -f "${functions_include}" ]; then
    . "${functions_include}"
else
    echo "${functions_include} not present.  Exiting " 1>&2
    exit 1
fi

MAPNAME=${1,,}
if [ -z "${MAPNAME}" ]; then
    echoerr "ERROR: No language provided.  Run change_keyboard.sh <%COUNTRY_CODE%>"
    exit 2
fi

# quit if not running with admin privs
require_root

# Change keymap for current session
if ! loadkeys "${MAPNAME}" > /dev/null; then
    echoerr "ERROR: Could not set ${MAPNAME} for current session"
    exit 3
else
    echo "Changed keymap for this session to ${MAPNAME}"
fi

# Change keymap for future sessions
if ! grep -q '^XKBLAYOUT=' /etc/default/keyboard; then
    if ! echo "XKBLAYOUT=\"${MAPNAME}\"" >> /etc/default/keyboard; then
        echoerr "ERROR: Could not set persistent keymap to ${MAPNAME}"
        exit 4
    fi
else
    if ! sed -i "s/^XKBLAYOUT=.*/XKBLAYOUT=\"${MAPNAME}\"/" /etc/default/keyboard; then
        echoerr "ERROR: Could not set persistent keymap to ${MAPNAME}"
        exit 4
    fi
fi
echo "Changed keymap persistently to ${MAPNAME}"
