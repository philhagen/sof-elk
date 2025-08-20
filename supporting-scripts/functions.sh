# SOF-ELK® Supporting script
# (C)2025 Lewes Technology Consulting, LLC
#
# This file contains common functions for use in other bash scripts

# bash function to echo to STDERR instead of STDOUT
# source: https://stackoverflow.com/a/2990533/1400064
function echoerr() {
  echo "$@" 1>&2;
}

function require_root() {
    if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root.  Exiting."
    exit 1
    fi
}

function is_valid_ipv4() {
  local ip=$1
  local octets=(${ip//./ })
  if [ ${#octets[@]} -ne 4 ]; then
    return 1
  fi
  for octet in "${octets[@]}"; do
    if ! [[ "$octet" =~ ^[0-9]+$ ]] || [ "$octet" -lt 0 ] || [ "$octet" -gt 255 ]; then
      return 1
    fi
  done
  return 0
}

function is_valid_ipv6() {
  local ip=$1
  if [[ "$ip" =~ ^(::)?[0-9a-fA-F]{1,4}(::?[0-9a-fA-F]{1,4}){1,7}(::)?$ ]]; then
    return 0
  fi
  return 1
}

function is_valid_ip() {
  local ip=$1
  if is_valid_ipv4 "$ip" || is_valid_ipv6 "$ip"; then
    return 0
  else
    return 1
  fi
}
