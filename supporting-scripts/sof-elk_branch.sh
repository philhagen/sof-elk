#!/bin/bash
# SOF-ELK® Supporting script
# (C)2025 Lewes Technology Consulting, LLC
#
# This script will perform all the necessary steps to check out an upstream
#   testing branch of the SOF-ELK repository to experiment with new features, etc.
#
# Usage: sudo test_branch.sh -b <%TEST_BRANCH_NAME%> [-f]

# include common functions
functions_include="/usr/local/sof-elk/supporting-scripts/functions.sh"
if [ -f ${functions_include} ]; then
    . ${functions_include}
else
    echo "${functions_include} not present.  Exiting " 1>&2
    exit 1
fi

# set local functions
usage() {
    echo "Usage: $0 [-h] -b <%BRANCH_NAME%> [-f]"
    exit 3
}

# set default values
FORCE=0

# parse options
while getopts ":b:fh" opt; do
  case "${opt}" in
    b) BRANCH=${OPTARG} ;;
    f) FORCE=1 ;;
    h) usage ;;
    \?)
        echoerr "ERROR: Invalid option: -${OPTARG}."
        exit 2
        ;;
  esac
done

# ensure a branch name is specified
if [ -z "${BRANCH}" ]; then
    echoerr "ERROR: Specify branch with '-b <%BRANCH_NAME%>' option."
    exit 3
fi

# quit if not running with admin privs
require_root

cd /usr/local/sof-elk/

# make sure the requested branch exists
if $( ! git ls-remote --heads origin | grep -q refs\/heads\/${BRANCH} ); then
    echoerr "ERROR: No such remote branch exists: ${BRANCH}."
    exit 4
fi

# make sure there are no local changes
if [[ $( git status --porcelain ) && $FORCE -eq 0 ]]; then
    echoerr "ERROR: You have local changes to this repository - will not overwrite without '-f' to force."
    echoerr "       Run 'git status' from the /usr/local/sof-elk/ directory to identify the local changes."
    echoerr "       Note that using '-f' will delete any modifications that have been made in this directory."
    exit 2
fi

# the requested branch exists - display a warning and escape path before making
#   any changes to the system
echo "It's STRONGLY recommended to create a VM snapshot if possible, or better yet,"
echo "  to only proceed on a system with no operational data.  You won't necessarily"
echo "  be able to return the system to its current/original state after testing."
echo
echo "To proceed at your own risk, press <Enter> to continue."
echo "To cancel this, press Ctrl-C."
read -r

# if there are local changes and -f was specified, discard all local changes
if [[ $( git status --porcelain ) && FORCE -eq 1 ]]; then
    git reset --hard > /dev/null
    git clean -fdx > /dev/null
fi

git remote set-branches --add origin ${BRANCH}
git fetch origin
git checkout ${BRANCH}

# the SKIP_HOOK followed by running post_merge.sh ensures the post-merge hook
#   will run regardless of whether the content updates.
SKIP_HOOK=1 sof-elk_update.sh | grep -v "Up-to-date"
post_merge.sh
