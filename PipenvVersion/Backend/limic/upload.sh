#!/bin/bash
nano -w setup.py &&
VERSION=$(cat setup.py | grep version | awk 'BEGIN {FS="'\''"} {print $2;}') &&
sed -e "s/==.*/==$VERSION/" -i "" docker/Dockerfile &&
nano -w docker/Dockerfile &&
git add setup.py docker/Dockerfile &&
git commit &&
git push origin master &&
python3.7 setup.py sdist &&
python3.7 -m twine upload dist/LiMiC-$VERSION.tar.gz &&
cd docker &&
(docker build -t limic . || (sleep 5 && docker build -t limic .)) &&
docker tag limic:latest wonderworks/limic:$VERSION &&
docker tag limic:latest wonderworks/limic:latest &&
docker login &&
docker push wonderworks/limic:$VERSION &&
docker push wonderworks/limic:latest &&
cd -
