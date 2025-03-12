#!/bin/bash

# List directories excluding books/.audiobookshelf-metadata
find /media/media -type d ! -path "/media/media/books/.audiobookshelf-metadata*" -printf "%P\n" > media.txt

# Append files inside /media/media/vids
find /media/media/vids -type f -printf "vids/%P\n" >> media.txt

echo "media.txt updated!"
