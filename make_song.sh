#!/bin/bash

mkdir -p ./gen
file=$(basename $1)
song=$(basename $1 | sed 's/.txt//g')

set -x
python ./transcribe_song.py "$1" ./gen/"$song".ly 
pushd ./gen
lilypond "$song".ly
popd 
if command -v open &>/dev/null; then
	open ./gen/"$song".pdf
elif command -v xdg-open &>/dev/null; then
	xdg-open ./gen/"$song".pdf
fi