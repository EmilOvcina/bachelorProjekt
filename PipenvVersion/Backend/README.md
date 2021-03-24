# LiMiC

LiMiC is short for Linear-infrastructure Mission Control.

## Install

LiMiC has the following requirements:
* Python >= 3.4
* [Pipenv](https://pipenv.pypa.io/en/latest/)

Installation is simple when using pipenv. Clone the repo and position yourself within the project:
```
git clone URL
cd sdu_imada/Backend
```
Install all the dependencies using Pipenv and enter the virtual environment:
```
pipenv install
pipenv shell
```

## Run

Once in the virtual environemnt you can run LiMiC with:
```
python -m limic serve auto Denmark
```
Or alternatively, it can be run from outside the virtual environemnt:
```
pipenv run python -m limic serve auto Denmark
```

When running on a server it is useful to add the following options:
```
--no-browser --host extermal.hostname --port internal.port --render-host external.hostname --render-port external.port --render-prefix external.prefix
```

## Help

```
python -m limic
```