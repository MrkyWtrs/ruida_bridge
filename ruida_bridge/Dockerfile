FROM ghcr.io/home-assistant/base:latest

RUN apk add --no-cache python3 py3-pip

COPY requirements.txt /requirements.txt
RUN pip3 install --break-system-packages --no-cache-dir -r /requirements.txt

COPY app.py /app.py
COPY web.py /web.py
COPY static /static
COPY run.sh /run.sh

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
