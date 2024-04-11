#!/bin/bash

USER_ID=${TASKWEAVER_UID:-10002}
GROUP_ID=${TASKWEAVER_GID:-10002}

echo "Starting with UID: $USER_ID, GID: $GROUP_ID"
useradd -u $USER_ID -o -m taskweaver
groupmod -g $GROUP_ID taskweaver

chown -R taskweaver:taskweaver /app

su taskweaver -c "python -m taskweaver.ces.kernel.launcher"

