FROM ubuntu:latest 

ARG WORKING_DIR=/app
ENV PYTHONUNBUFFERED=1
WORKDIR ${WORKING_DIR}
COPY ${GITHUB_WORKSPACE} /app

RUN apt update && apt upgrade -y \
    python3-pip && apt-get install python3.6 && \
    pip3 install -r requirements.txt && \
    apt autoremove -y

CMD ["python3", "web-s.py"]