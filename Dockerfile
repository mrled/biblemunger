FROM alpine:3.5
LABEL maintainer "me@micahrl.com"
COPY ["kjv.xml", "*.py", "biblemunger.config.default.json", "/srv/biblemunger/"]
COPY ["static", "/srv/biblemunger/static"]
COPY ["temple", "/srv/biblemunger/temple"]
COPY ["biblemunger.config.docker.json", "/srv/biblemunger/biblemunger.config.json"]
RUN \
    apk --no-cache upgrade && apk --no-cache add \
        python3 \
    && python3 -m ensurepip \
    && python3 -m pip install --upgrade \
        CherryPy \
        Mako \
        pip \
    && addgroup -S munger \
    && adduser -S -G munger munger \
    && mkdir /mungerdata \
    && touch /mungerdata/.keep \
    && chown -R munger:munger /mungerdata \
    && chmod -R a+rX /srv/biblemunger
VOLUME /mungerdata
USER munger
EXPOSE 80
CMD ["/usr/bin/python3", "/srv/biblemunger/__main__.py", "--initialize", "init"]
