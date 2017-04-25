FROM alpine:3.5
LABEL maintainer "me@micahrl.com"
RUN /bin/true \
    && apk --no-cache upgrade && apk --no-cache add \
        python3 \
    && python3 -m ensurepip \
    && python3 -m pip install --upgrade pip \
    && python3 -m pip install \
        CherryPy \
        Mako
RUN /bin/true \
    && addgroup -S munger \
    && adduser -S -G munger munger \
    && mkdir /mungerdata /srv/biblemunger \
    && touch /mungerdata/.keep

# Have to chown before adding the volume
RUN chown -R munger:munger /mungerdata
VOLUME /mungerdata

EXPOSE 8187
COPY ["kjv.xml", "*.py", "biblemunger.config.default.json", "/srv/biblemunger/"]
COPY ["static", "/srv/biblemunger/static"]
COPY ["temple", "/srv/biblemunger/temple"]
COPY ["biblemunger.config.docker.json", "/srv/biblemunger/biblemunger.config.json"]

# Have to chown after copying the files (setting USER before copying does *not* chown them to that user)
RUN chown -R munger:munger /srv/biblemunger

USER munger
CMD ["/usr/bin/python3", "/srv/biblemunger/__main__.py", "--initialize", "init"]
