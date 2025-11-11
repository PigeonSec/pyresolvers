FROM python:3.14-alpine

RUN apk add --no-cache shadow bash && \
    mkdir /pyresolvers && \
    adduser -D -h /pyresolvers -s /sbin/nologin pyresolvers

COPY . /pyresolvers/

WORKDIR /pyresolvers/

RUN chown -R pyresolvers:pyresolvers /pyresolvers && \
    python3 setup.py install

USER pyresolvers

ENTRYPOINT ["/usr/local/bin/pyresolvers"]
