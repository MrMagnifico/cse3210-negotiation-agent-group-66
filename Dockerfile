FROM python:3.9-rc-buster

RUN apt-get -y update && apt-get install -y jq
WORKDIR /usr/src/party
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["util/run.sh"]
