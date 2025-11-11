FROM python:3.14-alpine

RUN apk add --no-cache bash && \
    adduser -D -h /home/pyresolvers -s /sbin/nologin pyresolvers

USER pyresolvers

WORKDIR /home/pyresolvers

RUN pip install --no-cache-dir pyresolvers

ENTRYPOINT ["pyresolvers"]
