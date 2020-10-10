FROM python:3.9

RUN pip install --upgrade pip
COPY ./pumpdetector/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r ./requirements.txt
COPY ./pumpdetector ./pumpdetector
RUN pip install -e ./pumpdetector
COPY run_detector.py .

CMD [ "python", "run_detector.py" ]