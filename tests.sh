EXIT_CODE=0
trap "EXIT_CODE=1;" ERR

python -m unittest
flake8 setup.py test thumbframes_dl
mypy thumbframes_dl test

exit $EXIT_CODE
