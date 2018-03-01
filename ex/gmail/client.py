import sys, os, shutil, pprint, csv, traceback, json, datetime, pip, gzip, base64, zipfile
from time import mktime
from time import sleep



pip.main(['install', 'requests'])

import requests
KEY_TMP_DIR = 'tmp'+os.sep
class Client:
    
    
    def __init__(self, clientId, clientSecret, refreshToken,user, query, logging):
        self.clientId = clientId
        self.clientSecret = clientSecret
        self.refreshToken = refreshToken
        self.user = user 
        # limit to mails with attachment by default
        self.query = 'has:attachment ' + query
        self.logging = logging
        
    
    
    
    
    
    def downloadAttachments(self, since):
        if since:
            self.query += ' after:' + since
        ## Flow
        access_token = self.get_access_token(self.clientId, self.clientSecret, self.refreshToken)
        
        messages = self.get_messages(access_token, self.user, self.query)
        
        attachments = []
        if not messages or messages['resultSizeEstimate'] == 0:
            return attachments
        
        for message in messages['messages']:
            message_body = self.get_message(access_token, self.user, message['id'])
        
            self.logging.info("Parsing email with body: "+message_body['snippet'])
        
            for part in message_body['payload']['parts']:
                if 'attachmentId' in part['body']:
                    attachments.append(self.get_attachment(access_token, self.user, message['id'], part['body']['attachmentId'], part['filename']))
    
                    
        return attachments
    
    
    def get_access_token(self, client_id, client_secret, refresh_token):
        refresh_token_req = {
            'grant_type':    'refresh_token',
            'client_id':     client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token
        }
    
        r = requests.post('https://accounts.google.com/o/oauth2/token', data=refresh_token_req)
        data = json.loads(r.text)
        access_token = data['access_token']
        return access_token
    
    #def get_messages(self, access_token, user, q, next_page=''):
    #    get_messages_req ={
    #        'access_token': access_token,
    #        'q': q,
    #        'pageToken': next_page
    #    }
    
    #    user = user.replace('@', '%40')
    #    r = requests.get("https://www.googleapis.com/gmail/v1/users/"+user+"/messages", get_messages_req)
    #    print(r.text)
    
    #    return json.loads(r.text)
    
    def get_messages(self, access_token, user, q):
        get_messages_req ={
            'access_token': access_token,
            'q': q
        }
    
        user = user.replace('@', '%40')
        r = requests.get("https://www.googleapis.com/gmail/v1/users/"+user+"/messages", get_messages_req)
        return json.loads(r.text)
    
    def get_message(self, access_token, user, message_id):
        get_messages_req ={
            'access_token': access_token
        }
    
        user = user.replace('@', '%40')
        r = requests.get("https://www.googleapis.com/gmail/v1/users/"+user+"/messages/"+message_id, get_messages_req)
        return json.loads(r.text)        
    

    
    
    def get_attachment(self, access_token, user, message_id, attachment_id, filename):
        if filename[-4:] != '.zip':
            print("Skipping attachment: "+filename)
            return
    
        self.logging.info("Downloading attachment: "+filename)
    
        get_messages_req ={
            'access_token': access_token
        }
    
        user = user.replace('@', '%40')
        
        r = requests.get("https://www.googleapis.com/gmail/v1/users/"+user+"/messages/"+message_id+"/attachments/"+attachment_id, get_messages_req)
        response = json.loads(r.text)
    
        file_data = base64.urlsafe_b64decode(response['data'].encode('UTF-8'))
        if not os.path.exists(KEY_TMP_DIR):
                os.makedirs(KEY_TMP_DIR)
        with open(KEY_TMP_DIR+filename, 'wb') as f:
            f.write(file_data)
    
        return KEY_TMP_DIR+filename



