FROM acockburn/appdaemon:dev
RUN pip3 install --no-cache-dir pymysql \
 && apk add git
ARG CACHEBUST=1
RUN pip3 install -e git+https://github.com/mfugate1/sleepyq.git#egg=sleepyq
