FROM python:3.9

WORKDIR /usr/src/app
RUN pip install --upgrade pip
COPY ./vannpumpelogserver ./vannpumpelogserver
RUN pip install --no-cache-dir -r ./vannpumpelogserver/requirements.txt
RUN pip install -e ./vannpumpelogserver
COPY run_server.py .

CMD [ "python", "run_server.py" ]