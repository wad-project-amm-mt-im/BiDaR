# start by pulling the python image
FROM python:3.6.9-stretch

# switch working directory
RUN mkdir -p /app
WORKDIR /app

# copy every content from the local file to the image
COPY . /app
RUN apt-get update
#RUN yes | apt-get upgrade
RUN yes | apt install graphviz
# RUN pip install --upgrade pip
RUN pip install -r requirements.txt


