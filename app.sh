#!/bin/bash
pip install -q dash pandas numpy plotly 2>&1
export APP_PORT=8888
export APP_HOST=0.0.0.0
if [ -n "$DOMINO_RUN_HOST_PATH" ]; then
    export DASH_REQUESTS_PATHNAME_PREFIX="/$DOMINO_RUN_HOST_PATH"
fi
env | grep DASH_REQUESTS
env | grep DOMINO_RUN_HOST
python app.py 2>&1
