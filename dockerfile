FROM registry.git.domain.alex/lelik9/xenserver:latest

ADD client /home/client
ENTRYPOINT ["python"]
CMD [ "/home/client/backup_client.py" ]