FROM docker:5000/xenbackup-image:latest

CMD [ "rm", "-rf", "/home/xenserver-backup"]
ADD xenserver-backup /home/xenserver-backup
EXPOSE 5000
CMD [ "python", "/home/xenserver-backup/client/backup_client.py" ]