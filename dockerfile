FROM ubuntu:latest 

ARG WORKING_DIR=/app
WORKDIR ${WORKING_DIR}
COPY ${GITHUB_WORKSPACE} /app

RUN apt update && apt upgrade -y \
    python3-pip && apt-get install python3.6 && \
    pip3 install -r requirements.txt && \
    apt autoremove -y
# RUN pip3 install gevent flask boto3 awscli --- if requirements.txt dont have them specified and you dont want them in

EXPOSE 5000
# Add others like 22 etc if you would like to ssh into the pod but not necessary

CMD ["python3", "web-s.py"]
# ^ uncomment when you are able to run app locally succesful.