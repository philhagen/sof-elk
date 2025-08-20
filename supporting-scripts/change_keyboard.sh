#!/bin/bash
# SOF-ELK® Supporting script
# (C)2025 Lewes Technology Consulting, LLC
# (C)2018 505 Forensics
#
# This script will assist in making temporary and permanent changes to the
# keyboard layout in SOF-ELK to facilitate international keyboards.
# Usage:
# sudo change_keyboard.sh <country_code>

# Keyboard country codes are typically two-letters (IT, DE, JP, etc.)
# The script will error out if an incorrect code is provided.

if [ -f /usr/local/sof-elk/supporting_scripts/functions.sh ]; then
    . /usr/local/sof-elk/supporting_scripts/functions.sh
fi

require_root

# Temporary keymap change
loadkeys $1 > /dev/null
echo "Changed keymap for this session to ${1}"

# Permanent keymap change
sed -i 's/^keymap=/keymap=$1/g' /etc/default/grub
grub2-mkconfig -o /boot/grub2/grub.cfg > /dev/null 2>/dev/null
echo "Changed keymap persistently to ${1}"