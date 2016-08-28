FROM docker:5000/xenbackup-image:latest

CMD [ "rm", "-rf", "/home/xenserver"]
ADD xenserver /home/xenserver
EXPOSE 5000
CMD [ "python", "/home/xenserver/client/backup_client.py" ]