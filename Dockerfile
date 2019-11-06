FROM python:2
LABEL maintainer="Ilya Bumarskov <bumarskov@gmail.com>"

COPY etc /testrail_reporter/etc
COPY lib /testrail_reporter/lib
COPY reporter.py /testrail_reporter/
COPY requirements.txt /testrail_reporter/

WORKDIR /testrail_reporter

RUN pip install -r requirements.txt
