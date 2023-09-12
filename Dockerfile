FROM mysql:8.0-debian as build
ENV MYSQL_ROOT_PASSWORD=root
COPY . /app
RUN \
    apt-get -y update && apt-get -y upgrade \
    && apt install -y -q \
        python3 python3-pip \
    && apt-get autoremove --purge -y \
    && pip3 install -r /app/requirements.txt \
    && UN pip3 install --no-cache-dir -r requirements
    && apt-get clean -y \
    && chmod -R 777 /app \
    && rm -rf /app/venv \
    && rm -rf /app/effect picture \ 
#    && rm /app/magnet/*.txt \
    && rm /entrypoint.sh \
    && rm /app/logs/*.log \
    && find /app -name "__pycache__" -print0 | xargs -0 rm -rf \
    && find /app -name ".*" -print0 | xargs -0 rm -rf \
#    && rm /usr/local/bin/docker-entrypoint.sh \
    && cp /app/mysql_init/mysql_init.sql /docker-entrypoint-initdb.d

ENTRYPOINT ["/app/docker-entrypoint.sh"]

#EXPOSE 3306 33060
CMD ["mysqld"]