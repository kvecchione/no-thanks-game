import os
from mongoengine import connect


mongo_host = os.environ.get('MONGODB_HOST')
if mongo_host:
    connect('nothanks', host=mongo_host)
else:   
    connect('nothanks')
