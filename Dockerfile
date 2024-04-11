FROM python:alpine

RUN apk add gcc
RUN pip install --upgrade pip
RUN pip install kubernetes
RUN MULTIDICT_NO_EXTENSIONS=1 pip install kopf
ADD ./xlscsde /src/xlscsde
ADD ./service.py /src/service.py
COPY --chmod=0777 ./startup.sh /src/startup.sh

CMD "/src/startup.sh"