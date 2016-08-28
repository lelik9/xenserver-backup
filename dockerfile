FROM docker:5000/xenbackup-image:latest

CMD [ "rm", "-rf", "/home/client"]
ADD client /home/client
EXPOSE 5000
ENTRYPOINT ["python"]
CMD [ "/home/client/backup_client.py" ]