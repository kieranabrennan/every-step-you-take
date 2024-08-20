from gmail_reader import GmailReader
from firestore_service import FirestoreService
import re
from datetime import datetime
import logging

def parse_email_to_dict(email_contents):
    '''
    Takes the contents of the steps email
    Returns a dataframe with date and step_count columns
    '''
    body = email_contents['body']
    # Remove HTML tags and split by line
    lines = re.sub(r'<br/>', '\n', body).strip().split('\n')
    
    # Parse each line into date and step_count, converting date format and step_count to int
    data_dict = {}
    for line in lines:
        date_str, step_count_str = line.split(', ')
        # Convert date format from '10 Aug 2024' to '2024-08-10'
        date = datetime.strptime(date_str, '%d %b %Y').strftime('%Y-%m-%d')
        # Convert step_count to integer
        step_count = int(step_count_str)
        # Add to dictionary
        data_dict[date] = step_count

    return data_dict

def save_unread_step_emails_to_firestore():
    gmail_reader = GmailReader()
    firestore_service = FirestoreService()
    unread_email_list = gmail_reader.get_unread_emails()
    
    for unread_email in unread_email_list:
        email_contents = gmail_reader.get_email_contents(unread_email['id'])
        steps_dict = parse_email_to_dict(email_contents)
        
        firestore_service.upload_dict(steps_dict, field_name='step_count')
        gmail_reader.mark_email_as_read(unread_email['id'])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    save_unread_step_emails_to_firestore()