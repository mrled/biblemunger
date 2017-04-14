FROM alpine:3.5
LABEL maintainer "me@micahrl.com"
RUN apk --no-cache upgrade && apk --no-cache add \
    python3
RUN python3 -m ensurepip && python3 -m pip install --upgrade \
    CherryPy \
    Mako \
    pip
COPY ["kjv.xml", "*.py", "biblemunger.config.default.json", "/srv/biblemunger/"]
COPY ["static", "/srv/biblemunger/static"]
COPY ["temple", "/srv/biblemunger/temple"]
COPY ["biblemunger.config.docker.json", "/srv/biblemunger/biblemunger.config.json"]
RUN addgroup -S munger && adduser -S -G munger munger
RUN mkdir /mungerdata && touch /mungerdata/.keep && chown -R munger:munger /mungerdata
VOLUME /mungerdata
USER munger
EXPOSE 80
CMD ["/usr/bin/python3", "/srv/biblemunger/__main__.py", "--initialize", "init"]
