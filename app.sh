#!/bin/bash
pip install -q dash pandas numpy plotly 2>&1
export APP_PORT=8888
export APP_HOST=0.0.0.0
python app.py 2>&1
