FROM ubuntu:yakkety

ENV LANG C.UTF-8

RUN apt-get update && apt-get install --no-install-recommends -y \
    gir1.2-gtk-3.0 \
    python3-flake8 \
    python3-gi \
    python3-gi-cairo \
    python3-pytest
