#!/bin/bash
# SOF-ELK® Supporting script
# (C)2024 Lewes Technology Consulting, LLC
#
# This script is used to update the repository from its git origin
# It will not overwrite any local changes unless -f (force) is specified

FORCE=0

# bash function to echo to STDERR instead of STDOUT
# source: https://stackoverflow.com/a/2990533/1400064
echoerr() {
  echo "$@" 1>&2;
}

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root.  Exiting."
  exit 1
fi

while getopts ":f" opt; do
  case "${opt}" in
    f) FORCE=1 ;;
    ?)
      echoerr "ERROR: Invalid option: -${OPTARG}."
      exit 2
      ;;
  esac
done

cd /usr/local/sof-elk/ || exit 3
if [[ $( git status --porcelain ) && $FORCE -eq 0 ]]; then
  echoerr "ERROR: You have local changes to this repository - will not overwrite without '-f' to force."
  echoerr "       Run 'git status' from the /usr/local/sof-elk/ directory to identify the local changes."
  echoerr "       Note that using '-f' will delete any modifications that have been made in this directory."
  exit 2
fi

/usr/local/sof-elk/supporting-scripts/git-remote-update.sh -now
# This method adapted from method here: https://stackoverflow.com/a/3278427
LOCAL=$(git rev-parse "@{0}")
REMOTE=$(git rev-parse "@{u}")
BASE=$(git merge-base "@{0}" "@{u}")

if [[ "${LOCAL}" == "${REMOTE}" ]]; then
  echo "Up-to-date"

elif [[ "${LOCAL}" == "${BASE}" ]]; then
  # Need to pull
  git reset --hard > /dev/null
  git clean -fdx > /dev/null
  git pull origin

  /usr/local/sof-elk/supporting-scripts/git-remote-update.sh -now
  for lspid in $( pgrep -u logstash java ); do
      kill -s HUP "${lspid}"
  done

elif [[ "${REMOTE}" == "${BASE}" ]]; then
  echo "Need to push - this should never happen"

else
  echo "Diverged - this should never happen"
fi
