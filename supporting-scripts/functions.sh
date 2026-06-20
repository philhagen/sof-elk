# SOF-ELK® Supporting script
# (C)2026 Lewes Technology Consulting, LLC
#
# This file contains common functions for use in other bash scripts

# bash function to echo to STDERR instead of STDOUT
# source: https://stackoverflow.com/a/2990533/1400064
function echoerr() {
    echo "$@" 1>&2;
}

function require_root() {
    if [[ $EUID -ne 0 ]]; then
        echoerr "This script must be run as root.  Exiting."
        exit 1
    fi
}

function is_valid_ipv4() {
    local ip=$1
    local octets
    IFS='.' read -ra octets <<< "$ip"
    if [ ${#octets[@]} -ne 4 ]; then
        return 1
    fi
    for octet in "${octets[@]}"; do
        if [[ "$octet" == "" ]] || ! [[ "$octet" =~ ^(0|[1-9][0-9]{0,2})$ ]] || [ "$octet" -lt 0 ] || [ "$octet" -gt 255 ]; then
            return 1
        fi
    done
    return 0
}

function is_valid_ipv6() {
    local ip=$1
    local h="[0-9a-fA-F]{1,4}"
    local v4="((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])"

    local re="^("
    re+="(${h}:){7}${h}"                        # 1:2:3:4:5:6:7:8
    re+="|(${h}:){1,7}:"                         # 1::   1:2:3:4:5:6:7::
    re+="|(${h}:){1,6}:${h}"                     # 1::8   1:2:3:4:5:6::8
    re+="|(${h}:){1,5}(:${h}){1,2}"              # 1::7:8 1:2:3:4:5::7:8
    re+="|(${h}:){1,4}(:${h}){1,3}"              # 1::6:7:8
    re+="|(${h}:){1,3}(:${h}){1,4}"              # 1::5:6:7:8
    re+="|(${h}:){1,2}(:${h}){1,5}"              # 1::4:5:6:7:8
    re+="|${h}:((:${h}){1,6})"                   # 1::3:4:5:6:7:8
    re+="|:((:${h}){1,7}|:)"                     # ::2:3:4:5:6:7:8   and   ::
    re+="|fe80:(:${h}){0,4}%[0-9a-zA-Z]+"        # fe80::7:8%eth0 (link-local with zone)
    re+="|::(ffff(:0{1,4})?:)?${v4}"             # ::ffff:1.2.3.4 (IPv4-mapped)
    re+="|(${h}:){1,4}:${v4}"                    # 1:2:3:4::1.2.3.4
    re+=")$"

    if [[ "$ip" =~ $re ]]; then
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
