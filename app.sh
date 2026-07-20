#!/bin/bash
echo "Installing dependencies..."
pip install -q dash pandas numpy plotly 2>&1
echo "Starting app on port 8888..."
export APP_PORT=8888
export APP_HOST=0.0.0.0
python app.py 2>&1
