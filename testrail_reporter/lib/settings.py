import os

# TestRail Reporter (TRR)
TRR_LOG_FILE = os.environ.get(
    "TRR_LOG_FILE", os.path.join(os.getcwd(), 'testrail-reporter.log')
)
TRR_LOG_LEVEL = os.environ.get("TRR_LOG_LEVEL", "DEBUG")
TRR_TITLE_MAX_LENGTH = int(os.environ.get("TRR_TITLE_MAX_LENGTH", 250))
