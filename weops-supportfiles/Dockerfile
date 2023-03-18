FROM python:3.6.8

WORKDIR /opt
ADD ./apps .
ADD ./bin .
ADD ./blueking .
ADD ./official_plugin .
ADD ./bkoauth .
ADD ./common .
ADD ./locale .
ADD ./pipeline .
ADD ./version_log .
ADD ./script_tools .
ADD ./config .
ADD ./upgrade .
ADD ./env .
ADD ./manage.py .
ADD ./settings.py .

ADD ./app.yml .
ADD ./urls.py .
ADD ./wsgi.py .
ADD ./requirements.txt .
ADD ./VERSION .
ADD ./version_log .
ADD ./VERSION .
ADD ./release .
RUN mkdir ./version_logs_html
ADD ./projects.yaml .
ADD ./support-files .
RUN rm -Rf ./config/local_settings.py
RUN pip3 install -i https://mirrors.cloud.tencent.com/pypi/simple -U pip
RUN pip3 install -i https://mirrors.cloud.tencent.com/pypi/simple -r ./requirements.txt
