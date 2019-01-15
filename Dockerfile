FROM python:3.6-stretch
FROM alpacamarkets/pylivetrader

ARG APCA_API_SECRET_KEY
ARG APCA_API_KEY_ID
ARG APCA_API_BASE_URL

ENV APCA_API_SECRET_KEY=$APCA_API_SECRET_KEY
ENV APCA_API_KEY_ID=$APCA_API_KEY_ID
ENV APCA_API_BASE_URL=$APCA_API_BASE_URL

RUN mkdir /app

COPY . /app

WORKDIR /app

CMD pylivetrader run -f strategywoo.py
#CMD pylivetrader run -f algo.py
#CMD docker run -v $PWD:/work -w /work alpacamarkets/pylivetrader pylivetrader run -f algo.py
