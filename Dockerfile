FROM python:2.7-alpine

COPY . /marathon-release
RUN  apk update && \
     apk add ca-certificates wget && \
     update-ca-certificates && \
     adduser -u 1000 -D user  && \
     cd /marathon-release && \
     python setup.py install

USER user
WORKDIR /release


