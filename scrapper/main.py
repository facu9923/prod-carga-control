import os
import time
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import re
import scrapper_cruce
import scrapper_petrotandil
import scrapper_petro2 
import fitz # PyMuPDF
from unidecode import unidecode
import boto3
from io import BytesIO

# Configuración de los alcances y la ruta de guardado
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def upload_to_s3(file_path, bucket_name, s3_key):
    s3 = boto3.client('s3')
    try:
        # Subir archivo a S3
        s3.upload_file(file_path, bucket_name, s3_key)
        url = f"https://cargacontrolbucket.s3.amazonaws.com/{s3_key}"
        print(f"Archivo subido con éxito. URL: {url}")
        return url
    except Exception as e:
        print(f"Error al subir el archivo: {e}")
        return None
    
def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_service():
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)
    return service

def download_attachment(service, msg_id, attachment_id, filename, subject_value):
    attachment = service.users().messages().attachments().get(userId='me', messageId=msg_id, id=attachment_id).execute()
    file_data = base64.urlsafe_b64decode(attachment['data'])
    # BUCKET NAME CONEXION

    if subject_value == "cruce":
        print("Subiendo al bucket cruce")
        s3_key = f"cruce/{filename}"
        
        try:
            # Crear un nuevo BytesIO para S3
            s3_stream = BytesIO(file_data)
            s3 = boto3.client('s3')
            s3.upload_fileobj(s3_stream, bucket_name, s3_key)
            url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
            print(f"Archivo PDF subido con éxito. URL: {url}")

            # Crear un nuevo BytesIO para fitz
            pdf_stream = BytesIO(file_data)
            doc = fitz.open("pdf", pdf_stream)
            scrapper_cruce.get_data_cruce(doc, url)
            doc.close()
            pdf_stream.close()
        except Exception as e:
            print(f"Error al procesar cruce: {e}")

    elif subject_value == "petrotandil":
        print("Subiendo al bucket petrotandil")
        s3_key = f"petro/{filename}"

        try:
            # Crear un nuevo BytesIO para S3
            s3_stream = BytesIO(file_data)
            s3 = boto3.client('s3')
            s3.upload_fileobj(s3_stream, bucket_name, s3_key)
            url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
            print(f"Archivo PDF subido con éxito. URL: {url}")

            # Crear un nuevo BytesIO para fitz
            pdf_stream = BytesIO(file_data)
            doc = fitz.open("pdf", pdf_stream)
            scrapper_petrotandil.get_data_petro(doc, url)
            doc.close()
            pdf_stream.close()
        except Exception as e:
            print(f"Error al procesar petrotandil: {e}")

    elif subject_value == "petrotandil2":
        print("Subiendo al bucket petrotandil2")
        s3_key = f"petro2/{filename}"

        try:
            # Crear un nuevo BytesIO para S3
            s3_stream = BytesIO(file_data)
            s3 = boto3.client('s3')
            s3.upload_fileobj(s3_stream, bucket_name, s3_key)
            url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
            print(f"Archivo PDF subido con éxito. URL: {url}")

            # Crear un nuevo BytesIO para fitz
            pdf_stream = BytesIO(file_data)
            doc = fitz.open("pdf", pdf_stream)
            scrapper_petro2.get_data_petro2(doc, url)
            doc.close()
            pdf_stream.close()
        except Exception as e:
            print(f"Error al procesar petrotandil2: {e}")
    else:
        print("Asunto desconocido")

def delete_extra(texto):
    texto = unidecode(texto.lower())
    print(texto)
    # Buscar las palabras clave
    if 'electronica' in texto or 'corriente' in texto or 'recibo' in texto or 'listado' in texto:
        return ''
    if 'petrotandil' in texto and 'venta' in texto:
        return 'petrotandil2'
    if 'petrotandil' in texto:
        return 'petrotandil'
    if 'cruce' in texto:
        return 'cruce'
    if 'electornica' in texto or 'corriente' in texto or 'recibo' in texto or 'listado' in texto:
        return ''
    

    
def check_new_emails(service):
    # Timestamp de 5 minutos atrás
    timestamp_five_minutes_ago = datetime.now() - timedelta(seconds=29)
    timestamp_unix = int(timestamp_five_minutes_ago.timestamp())

    # Obtiene los mensajes sin leer en la bandeja de entrada
    query = f'(subject:"EL CRUCE" OR subject:"el cruce" OR subject:"PETROTANDIL" OR subject:"petrotandil") AND after:{timestamp_unix}'


    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q=query).execute()
    messages = results.get('messages', [])

    print(f"Mensajes sin leer encontrados: {len(messages)}")

    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()

        subject = msg['payload'].get('headers', [])
        subject_value = next((header['value'] for header in subject if header['name'] == 'Subject'), None)
        subject_value = delete_extra(subject_value)
        
        for part in msg['payload'].get('parts', []):
            if part['filename'] and part['filename'].endswith('.pdf'):
                print(f"PDF encontrado: {part['filename']} y el asunto es: {subject_value}")
                if 'attachmentId' in part['body']:
                        download_attachment(service, msg['id'], part['body']['attachmentId'], part['filename'], subject_value)
                else:
                    print("No se encontró data ni attachmentId en el archivo PDF.")
        # Marca el mensaje como leído
        service.users().messages().modify(userId='me', id=message['id'], body={'removeLabelIds': ['UNREAD']}).execute()
        print(f"Mensaje {message['id']} marcado como leído.")

if __name__ == '__main__':
    service = get_service()
    print("Iniciando verificación de correos...")
    while True:
        check_new_emails(service)
        print("Esperando 30 segundos antes de la próxima verificación...")
        time.sleep(30)  # Espera 60 segundos antes de verificar nuevamente
