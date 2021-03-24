#!bin/bash
_self="${0##*/}"
FILE=backend/venv

if [ ! -d $FILE ]
then
	echo "INSTALLING"
	python3 -m venv "backend/venv/"
	source ./backend/venv/bin/activate
	pip install -r requirements.txt
	rm -r "backend/venv/lib/python3.9/site-packages/limic" 
	cp -r "limic" "backend/venv/lib/python3.9/site-packages/limic" 

	cd ./backend/
	source ./venv/bin/activate
	python -m limic serve npz graph.Denmark.npz ../leaflet/index.html --no-browser
	deactivate 
else
	rm -r "backend/venv/lib/python3.9/site-packages/limic" 
	cp -r "limic" "backend/venv/lib/python3.9/site-packages/limic"
	cd ./backend/
	source ./venv/bin/activate
	python -m limic serve npz graph.Denmark.npz ../leaflet/index.html --no-browser
	deactivate 
fi