#!/usr/bin/env bash
cd ./pythonProject/
source ./venv/bin/activate
python -m limic serve npz graph.Denmark.npz ../leaflet/index.html --no-browser
deactivate 