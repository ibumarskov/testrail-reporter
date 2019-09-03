FROM python:2
LABEL maintainer="Ilya Bumarskov <bumarskov@gmail.com>"

COPY etc /qa_reports/etc
COPY lib /qa_reports/lib
COPY qa_report.py /qa_reports/
COPY entrypoint.sh /qa_reports/
COPY requirements.txt /qa_reports/

WORKDIR /qa_reports

RUN pip install -r requirements.txt
