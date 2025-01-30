FROM python:3.12.8-alpine3.21

RUN apk add gcc
RUN pip install --upgrade pip
RUN pip install kubernetes
RUN MULTIDICT_NO_EXTENSIONS=1 pip install kopf
COPY --chmod=0777 ./xlscsde /src/xlscsde
COPY --chmod=0777 ./service.py /src/service.py
COPY --chmod=0777 ./startup.sh /src/startup.sh

CMD "/src/startup.sh"

ENV MANAGED_BY="secrets-distributor"
ENV SECRETS_PATH="/mnt/secrets"

USER 101