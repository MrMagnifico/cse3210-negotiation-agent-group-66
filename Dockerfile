FROM python:3.9-rc-buster

WORKDIR /usr/src/party
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python3 setup.py sdist

FROM tomcat:8
WORKDIR /usr/local/tomcat/webapps
RUN apt-get -y update && apt-get -y install python3-pip python3-venv
RUN wget "http://artifactory.ewi.tudelft.nl/artifactory/libs-release-local/geniusweb/pypartiesserver/2.1.0/pypartiesserver-2.1.0.war"

ENV PYTHON3EXE /usr/bin/python3

COPY --from=0 /usr/src/party/dist /usr/local/tomcat/webapps
CMD ["catalina.sh", "run"]
