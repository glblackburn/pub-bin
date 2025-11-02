#!/bin/bash

find . -name "*~"

echo "remove these? [y/n]"
read response
if [ "$response" == 'y' ] ; then
    find . -name "*~" -exec rm {} \;
else
    echo "NOT REMOVED"
fi
