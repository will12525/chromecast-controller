#!/bin/bash
trap 'kill 0' SIGTERM

ln -s /install/node_modules /app/app/static/

# Start HTTP servers and capture their PIDs
#cd /media/library && http-server -p 8000 &
cd /media/ && http-server -p 8000 &
PID1=$!
echo "HTTP server 1 PID: $PID1"

cd /media/library_2 && http-server -p 8001 &
PID2=$!
echo "HTTP server 2 PID: $PID2"

cd /media/raw_files && http-server -p 8002 &
PID3=$!
echo "HTTP server 3 PID: $PID3"

# Run the main command
cd /app
${CMD}
CMD_EXIT_CODE=$?

# Kill background processes using their PIDs and exit with the same code as ${CMD}
kill $PID1 $PID2 $PID3
exit $CMD_EXIT_CODE
