FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /workspace/Tools/MotionBoard
COPY server.py /workspace/Tools/MotionBoard/server.py

# The supplied Compose file mounts the frontend and private libraries read-only.
# No pip packages, model downloads, or host packages are installed.
CMD ["python", "server.py"]
