#!/bin/bash
# update the repository from origin
FORCE=0

# parse any command line arguments
if [ $# -gt 0 ]; then
    while true; do
        if [ $1 ]; then
            if [ $1 == '-force' ]; then
                FORCE=1
            fi
            shift
        else
            break
        fi
    done
fi

cd /usr/local/sof-elk/
if [[ $( git status --porcelain ) && $FORCE -eq 0 ]]; then
    echo "ERROR: You have local changes to this repository - will not overwrite without '-force'."
    echo "       Note that using '-force' will delete any modifications made in the /usr/local/sof-elk/ directory."
    exit 2
fi

git reset --hard > /dev/null
git pull origin