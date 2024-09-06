import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from credentials import set_credentials_env_var

from google.cloud import storage
import base64
import logging

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']

class GmailReader:
    '''Service for Gmail. Read emails'''

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        set_credentials_env_var()

        self.token_bucket_name = 'gmail_token_bucket'
        self.token_file_name = 'gmail_token.json'

        self.TOKEN_FILE = 'gmail_token.json'
        self.CREDENTIAL_FILE = 'oauth_credentials.json'
        
        self.creds = None
        self.authenticate()

    def authenticate(self):
        ''' Authenticates the Gmail account
        Checks cloud storage bucket for token, and handles token refreshing
        If no token, follows OAuth flow for authentication and to create and save a token
        '''
        try:
            self.ensure_bucket_exists()
            self.creds = self.load_token_from_cloud_storage()

            # If there are no (valid) credentials available, let the user log in.
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    try:
                        self.logger.info("Attempting to refresh token")
                        self.creds.refresh(Request())
                    except Exception as e:
                        self.logger.error(f"Error refreshing token: {e}")
                        self.delete_token_in_cloud_storage()
                        return self.authenticate()
                else:
                    self.get_new_credentials()
                # Save the credentials for the next run
                self.save_token_to_cloud_storage()
        
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            raise

    def get_new_credentials(self):
        """Initiates OAuth 2.0 flow to obtain new Gmail API credentials.
        """
        try:
            flow = InstalledAppFlow.from_client_secrets_file(self.CREDENTIAL_FILE, SCOPES)
            self.creds = flow.run_local_server(port=0)
        except Exception as e:
            self.logger.error(f"Failed to get new credentials: {e}")
            raise

    def ensure_bucket_exists(self):
        ''' Ensure the Google Cloud Storage bucket exists, create if it doesn't '''
        try:
            storage_client = storage.Client()
            bucket = storage_client.lookup_bucket(self.token_bucket_name)
            if not bucket:
                bucket = storage_client.create_bucket(self.token_bucket_name)
                self.logger.info(f"Bucket {self.token_bucket_name} created.")
            else:
                self.logger.info(f"Bucket {self.token_bucket_name} already exists.")
        except Exception as e:
            self.logger.error(f"Failed to check or create bucket: {e}")
            raise

    def load_token_from_cloud_storage(self):
        ''' Load the token from Google Cloud Storage '''
        try:
            storage_client = storage.Client()
            bucket = storage_client.get_bucket(self.token_bucket_name)
            blob = bucket.blob(self.token_file_name)
            token_json = blob.download_as_text()
            return Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
        except Exception as e:
            self.logger.error(f"Failed to load token from cloud storage: {e}")
            return None

    def save_token_to_cloud_storage(self):
        ''' Save the token to Google Cloud Storage '''
        try:
            storage_client = storage.Client()
            bucket = storage_client.get_bucket(self.token_bucket_name)
            blob = bucket.blob(self.token_file_name)
            blob.upload_from_string(self.creds.to_json())
            self.logger.info("Token successfully saved to cloud storage.")
        except Exception as e:
            self.logger.error(f"Failed to save token to cloud storage: {e}")

    def delete_token_in_cloud_storage(self):
        ''' Delete the token in Google Cloud Storage '''
        try:
            storage_client = storage.Client()
            bucket = storage_client.get_bucket(self.token_bucket_name)
            blob = bucket.blob(self.token_file_name)
            blob.delete()
            self.logger.info("Invalid token deleted from cloud storage.")
        except Exception as e:
            self.logger.error(f"Failed to delete token from cloud storage: {e}")

    def _get_emails(self, query=None):
        """ Fetches a list of emails based on the provided query.
            query (str): The query to filter emails. For example, "is:unread" for unread emails.
            list: A list of dictionaries, each containing 'id' and 'subject'.
        """
        try:
            self.logger.info("Getting emails")
            service = build('gmail', 'v1', credentials=self.creds)
            results = service.users().messages().list(userId='me', labelIds=['INBOX'], q=query).execute()
            messages = results.get('messages', [])
            email_list = []

            if not messages:
                self.logger.info('No messages found.')
            else:
                for message in messages:
                    email_list.append(self._extract_email_data(service, message['id']))

            return email_list

        except HttpError as error:
            self.logger.error(f"Error fetching emails: {str(error)}")
            return []
    
    def _extract_email_data(self, service, message_id):
        """Extracts the subject from a specific email.
            service: The Gmail API service instance.
            message_id (str): The ID of the email to be fetched.
        Returns:A dictionary containing 'id' and 'subject'.
        """
        try:
            self.logger.info("Extracting email contents")
            msg = service.users().messages().get(userId='me', id=message_id).execute()
            email_data = msg['payload']['headers']
            subject = None
            for values in email_data:
                if values['name'] == 'Subject':
                    subject = values['value']
                    break
            return {'id': message_id, 'subject': subject}

        except HttpError as error:
            self.logger.error(f"Error extracting email data for ID {message_id}: {str(error)}")
            return {'id': message_id, 'subject': 'Unknown'}

    def get_all_emails(self):
        """
        Returns: a list of dictionaries, each containing 'id' and 'subject'.
        """
        return self._get_emails()

    def get_unread_emails(self):
        """
        Fetches a list of unread emails in the inbox.
        Returns a list of dictionaries, each containing 'id' and 'subject'.
        """
        return self._get_emails(query="is:unread")

    def mark_email_as_read(self, message_id):
        """Marks an email as read by removing the 'UNREAD' label.
            message_id (str): The ID of the email to be marked as read.
        Returns: a bool, True if the email was successfully marked as read, False otherwise.
        """
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            # Modify the message to remove the 'UNREAD' label
            service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            self.logger.info(f"Email with ID {message_id} marked as read.")
            return True

        except HttpError as error:
            self.logger.error(f"Error marking email with ID {message_id} as read: {str(error)}")
            return False

    def get_email_contents(self, message_id):
        """Fetches the content of a specific email by its ID.
            message_id (str): The ID of the email to be read.
        Returns: A dictionary containing the email subject and body.
        """
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            msg = service.users().messages().get(userId='me', id=message_id).execute()
            email_data = msg['payload']['headers']
            subject = None
            for values in email_data:
                if values['name'] == 'Subject':
                    subject = values['value']
                    break

            # Extract the email body
            body = None
            if 'parts' in msg['payload']:
                # The email has multiple parts
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        body = part['body']['data']
                        body = base64.urlsafe_b64decode(body).decode('utf-8')
                        break
            else:
                # The email is plain text and has no 'parts'
                body = msg['payload']['body']['data']
                body = base64.urlsafe_b64decode(body).decode('utf-8')

            return {'subject': subject, 'body': body}

        except HttpError as error:
            self.logger.error(f"Error reading email with ID {message_id}: {str(error)}")
            return None

def read_all_unread_emails():
    gmail_reader = GmailReader()
    all_emails = gmail_reader.get_unread_emails()
    print(all_emails)

    for email in all_emails:
        email_contents = gmail_reader.get_email_contents(email['id'])
        print(email_contents)
        # gc.mark_email_as_read(email['id'])

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    read_all_unread_emails()    