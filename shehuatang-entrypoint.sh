#!/bin/bash

#echo "看看有没有这个运行啊"
#echo '等待初始化 mysql'
##source docker-entrypoint.sh mysqld
#function mysql_is_run() {
#  port=$(netstat -lnt | grep 3306 | wc -l)
#  pid=$(ps -ef | grep mysql | grep -v grep | wc -l)
#  if [ $port -ne 1 ] && [ $pid -ne 2 ]; then
#    #    /data/3306/mysql start
#    sleep 1
#    mysql_is_run
#  else
#    echo "mysql running!!!"
#  fi
#}
#mysql_is_run
#echo '初始化 mysql 完毕'

echo '开始执行'
sleep 2
config=/config/config.yaml

if [ ! -f "$config" ]; then
  echo '没有发现配置文件 已经自动生成了一个 位置在 /config/config.yaml 可以再次运行和编辑'
  cp /app/config_docker.yaml /config/config.yaml
fi

#python3 /app/main.py
python3 /app/schedule_main.py