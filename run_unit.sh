# run all unit unittest
source devices/server104.env
export PYTHONWARNINGS="ignore:Unverified HTTPS request"
python -m unittest discover tests
