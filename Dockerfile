FROM mysql:8.0-debian as build
ENV MYSQL_ROOT_PASSWORD=root
RUN \
    apt-get -y update && apt-get -y upgrade \
    && apt-get install -y --no-install-recommends python3 python3-pip git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove --purge -y \
    && apt-get clean && apt-get autoclean \
    && git clone https://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@github.com/wangjunkai2022/sehuatang_reptile.git /app \
    && rm -rf /app/.git \
    && rm /app/.gitignore \
    && pip3 install --no-cache-dir -r /app/requirements.txt \
    && apt-get clean -y \
    && chmod -R 777 /app \
    && cp /app/mysql_init/mysql_init.sql /docker-entrypoint-initdb.d

VOLUME [ "/config" ]
ENTRYPOINT ["/app/docker-entrypoint.sh"]

#EXPOSE 3306 33060
CMD ["mysqld"]