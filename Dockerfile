FROM python

WORKDIR /Discord-music
COPY main.py .env requirements.txt /Discord-music

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install software-properties-common -y
#RUN add-apt-repository ppa:mc3man/trusty-media
RUN apt-get dist-upgrade
RUN apt-get install -y ffmpeg

RUN pip install --upgrade --force-reinstall 'https://github.com/ytdl-org/youtube-dl/archive/refs/heads/master.tar.gz'
RUN pip install -r requirements.txt

CMD python3 main.py