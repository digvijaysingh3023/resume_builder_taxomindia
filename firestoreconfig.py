import firebase_admin
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials,firestore,storage
load_dotenv()

firebase_config = {
    "type": os.getenv('FIREBASE_TYPE'),
    "project_id": os.getenv('FIREBASE_PROJECT_ID'),
    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
    "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
    "client_id": os.getenv('FIREBASE_CLIENT_ID'),
    "auth_uri": os.getenv('FIREBASE_AUTH_URI'),
    "token_uri": os.getenv('FIREBASE_TOKEN_URI'),
    "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL'),
    "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL'),
}

cred = credentials.Certificate(firebase_config)

firebase_admin.initialize_app(cred,{
    "storageBucket": os.getenv('STORAGE_BUCKET'),
})
db = firestore.client()
bucket = storage.bucket()
