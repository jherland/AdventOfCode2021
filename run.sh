#!/bin/sh

day=$1
if test -z "$day"; then
    day=$(date +%d)
fi

run() {
    echo "--- Running $1:"
    python3 "$1"
}

if test "$day" = "all"; then
    for f in ??.py; do
        run "$f"
    done
elif test -f "$day.py"; then
    run "$day.py"
else
    echo "Could not find $day.py"
    exit 1
fi
