FROM ubuntu:latest
LABEL authors="jstone@psi.edu"
ENV VALIDATE_VERSION=3.2.0
ENV VALIDATE_PACKAGE=validate-$VALIDATE_VERSION-bin.tar.gz
ENV VALIDATE_DIR=validate-$VALIDATE_VERSION

RUN apt-get update && apt-get install -y openjdk-8-jre-headless python3 python3-jinja2 python3-bs4 libcfitsio-bin && rm -rf /var/lib/apt/lists/*

ADD https://github.com/NASA-PDS/validate/releases/download/v$VALIDATE_VERSION/$VALIDATE_PACKAGE /opt
RUN cd /opt && tar -xzf $VALIDATE_PACKAGE && ln -s $VALIDATE_DIR validate && rm $VALIDATE_PACKAGE

COPY ingest /catalina/ingest
COPY schemas /catalina/schemas
COPY --chmod=544 catalina_run.sh /catalina/

ENTRYPOINT ["/catalina/catalina_run.sh"]