FROM python:3
WORKDIR /app
#COPY requirements.txt /app/requirements.txt
COPY . /app
RUN pip install --no-cache-dir -r /app/requirements.txt
#    && chmod -R 777 /app \
#    && rm -rf /app/venv \ 
#    && rm -rf /app/effect picture \ 
#    #    && rm /app/magnet/*.txt \
#    && rm /entrypoint.sh \
#    && rm /app/logs/*.log \
#    && find /app -name "__pycache__" -print0 | xargs -0 rm -rf \
#    && find /app -name ".*" -print0 | xargs -0 rm -rf \
#CMD ['python','/add/schedule_main.py']
