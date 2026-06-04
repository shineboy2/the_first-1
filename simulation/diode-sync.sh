#!/bin/sh

echo "Starting Data Diode Simulation..."

# Create necessary directories
mkdir -p /ftp-req/requests
mkdir -p /ftp-resp/requests
mkdir -p /ftp-resp/results /ftp-req/results
mkdir -p /ftp-resp/users /ftp-req/users
mkdir -p /ftp-resp/settings /ftp-req/settings
mkdir -p /ftp-resp/access /ftp-req/access
mkdir -p /ftp-resp/profiles /ftp-req/profiles

while true; do
  # Request -> Response (Upload requests)
  if [ -n "$(ls -A /ftp-req/requests 2>/dev/null)" ]; then
    echo "Syncing requests..."
    for file in /ftp-req/requests/*; do
      if [ -f "$file" ] && [ "${file##*.}" != "old" ]; then
        cp "$file" /ftp-resp/requests/ 2>/dev/null
        mv "$file" "$file.old" 2>/dev/null
      fi
    done
  fi

  # Response -> Request (Download results, users, settings, etc.)
  for dir in results users settings access profiles request_types; do
    mkdir -p /ftp-resp/$dir /ftp-req/$dir
    if [ -n "$(ls -A /ftp-resp/$dir 2>/dev/null)" ]; then
      echo "Syncing $dir..."
      for file in /ftp-resp/$dir/*; do
        if [ -f "$file" ] && [ "${file##*.}" != "old" ]; then
          cp "$file" /ftp-req/$dir/ 2>/dev/null
          mv "$file" "$file.old" 2>/dev/null
        fi
      done
    fi
  done

  sleep 5
done
