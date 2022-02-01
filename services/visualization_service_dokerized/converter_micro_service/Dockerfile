# start by pulling the python image
FROM python:3.7.12-alpine

# switch working directory
RUN mkdir -p /convert_micro
WORKDIR /convert_micro

# copy every content from the local file to the image
COPY . /convert_micro

RUN ls
RUN pwd

RUN pip install -r ./requirements.txt


