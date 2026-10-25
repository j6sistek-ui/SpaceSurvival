FROM python:3.11-slim-bookworm
WORKDIR /workspace
COPY Scripts/CryoComparison/ Scripts/CryoComparison/
COPY Scripts/CheckPrDocumentation.py Scripts/
COPY README.md PROJECT_STATE.md ./
COPY docs/KNOWN_ISSUES.md docs/PROJECT_STATE.md docs/PLAYTEST_TOMORROW.md docs/
CMD ["sh", "-c", "python -m compileall -q Scripts/CryoComparison && python Scripts/CheckPrDocumentation.py --repo ."]
