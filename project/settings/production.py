import os
import dj_database_url
from project.settings.base import *

SECRET_KEY = os.environ.get('SECRET_KEY')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
PATH_TO_FRONTEND = os.environ.get('PATH_TO_FRONTEND')
CORS_ORIGIN_WHITELIST = [PATH_TO_FRONTEND]

SIMPLE_JWT['SIGNING_KEY'] = SECRET_KEY

DEBUG = False

ALLOWED_HOSTS = ['juke-monster.herokuapp.com']

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
}

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
