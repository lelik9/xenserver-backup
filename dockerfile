FROM docker:5000/xenbackup-image:latest

CMD [ "rm", "-rf", "/home/client"]
ADD client /home/client
EXPOSE 5000
CMD [ "python", "/home/client/backup_client.py" ]