FROM ubuntu:latest 

ARG WORKING_DIR=/app
WORKDIR ${WORKING_DIR}
COPY ${GITHUB_WORKSPACE} /app

RUN apt update
RUN apt upgrade -y 
RUN apt install python3.8
RUN pip3 install requirements.txt
# RUN pip3 install gevent flask boto3 awscli --- if requirements.txt dont have them specified and you dont want them in

EXPOSE 5000
# Add others like 22 etc if you would like to ssh into the pod but not necessary

# CMD ["python3", "web-s.py"]
# ^ uncomment when you are able to run app locally succesful.