FROM alpine
MAINTAINER bouweceunen

RUN apk update \
  && apk add --update --no-cache python3 py-requests py3-pip \
  && pip3 install boto3

COPY backup.py backup.py
