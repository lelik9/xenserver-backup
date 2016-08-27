FROM docker:5000/xenbackup-image:latest

EXPOSE 5000
CMD [ "python", "/cclient/backup_client.py" ]