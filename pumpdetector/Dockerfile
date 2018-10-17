FROM python:3

RUN pip install --upgrade pip
COPY ./pumpdetector ./pumpdetector
RUN pip install --no-cache-dir -r ./pumpdetector/requirements.txt
RUN pip install -e ./pumpdetector
COPY run_detector.py .

CMD [ "python", "run_detector.py" ]