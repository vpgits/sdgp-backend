FROM ubuntu:latest
LABEL authors="vpmb"

ENTRYPOINT ["top", "-b"]