#!/bin/bash

mkdir -p ./gen
file=$(basename $1)
song=$(basename $1 | sed 's/.txt//g')

set -x
python ./transcribe_song.py "$1" ./gen/"$song".ly 
lilypond ./gen/"$song".ly
open ./gen/"$song".pdf