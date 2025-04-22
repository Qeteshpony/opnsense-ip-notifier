FROM python:3.13-alpine
COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements.txt
COPY *.py ./
CMD ["python3", "-u", "notify.py"]
