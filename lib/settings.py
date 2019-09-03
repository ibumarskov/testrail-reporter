import os

# QA Report (QAR)
QAR_LOG_FILE = os.environ.get(
    "QAR_LOG_FILE", os.path.join(os.getcwd(), '/var/log/qa_report.log')
)
QAR_LOG_LEVEL = os.environ.get("QAR_LOG_LEVEL", "DEBUG")
