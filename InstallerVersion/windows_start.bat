@ECHO OFF
SET file=backend\venv
if exist %file% (
	rmdir /q /s "backend\venv\Lib\site-packages\limic"
	xcopy "limic" "backend\venv\Lib\site-packages\limic\" /E
	echo Starting Limic
	cd backend\
	.\venv\Scripts\activate.bat
	python -m limic serve npz graph.Denmark.npz ../leaflet/index.html --no-browser
	deactivate
	cd ..
) else (
	echo Setting up the virtual environment
	python -m venv backend\venv\
	.\backend\venv\Scripts\activate.bat
	pip install -r requirements.txt
	deactivate
	rmdir /q /s "backend\venv\Lib\site-packages\limic"
	xcopy "limic" "backend\venv\Lib\site-packages\limic\" /E
	echo Installation Done

	echo Starting Limic
	cd backend\
	.\venv\Scripts\activate.bat
	python -m limic serve npz graph.Denmark.npz ../leaflet/index.html --no-browser
	deactivate
	cd ..
)