FROM python:3.8.2-slim

ENV DEBIAN_FRONTEND=noninteractive

ARG http_proxy
ARG https_proxy

ENV http_proxy $http_proxy
ENV https_proxy $https_proxy

WORKDIR /app

ENV DOCKERIZE_VERSION v0.6.1
ENV DOCKERIZE_URL https://github.com/jwilder/dockerize/releases/download

RUN apt-get update \
    && \
    apt-get -y --no-install-recommends install \
        build-essential wget \
    && \
    wget $DOCKERIZE_URL/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
            && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
            && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && \
    rm -rf /var/lib/apt/lists/* \
    && \
    rm -rf /var/cache/apt/archives/*

COPY requirements.txt ./

RUN pip install \
            -i https://test.pypi.org/simple/ \
            --extra-index-url=https://pypi.org/simple/ \
            --no-cache-dir \
            --trusted-host pypi.python.org \
            --trusted-host files.pythonhosted.org \
            --trusted-host pypi.org \
            --trusted-host test.pypi.org \
            -r requirements.txt \
    && \
    apt-get remove -y build-essential wget \
    && \
    apt-get autoremove -y

COPY . .

ENTRYPOINT ["docker-entrypoint.sh"]

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "stock_analysis.wsgi"]

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

