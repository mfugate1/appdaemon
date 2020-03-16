FROM acockburn/appdaemon:4.0.3

RUN pip3 install --no-cache-dir pymysql \
 && apk add git
 
COPY dockerStart.sh /usr/src/app
 
# Change the CACHEBUST variables to force the image to pick up changes from that repo

ARG SLEEPYQ_CACHEBUST=1
RUN pip3 install -e git+https://github.com/mfugate1/sleepyq.git#egg=sleepyq