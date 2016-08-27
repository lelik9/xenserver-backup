FROM docker:5000/xenbackup-image:latest

EXPOSE 5000
CMD [ "python", "/client/backup_client.py" ]