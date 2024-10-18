#!/bin/bash
# SOF-ELK® Supporting script
# (C)2024 Lewes Technology Consulting, LLC
#
# This runs scripts after a dhcp lease is secured or renewed

kill -HUP $( pidof agetty ) > /dev/null 2>&1
