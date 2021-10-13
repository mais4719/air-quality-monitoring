FROM python:3.7-buster

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        build-essential \
        less \
        python3-dev \
        vim \
        wget \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

CMD ["bash"]
