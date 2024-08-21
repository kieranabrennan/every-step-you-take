import logging
from flask import Flask
from firestore_service import FirestoreService
from step_count_plotter import StepCountPlotter
from email_sender import EmailSender
from gmail_reader import GmailReader
from gmail_to_firestore import parse_email_to_dict
import os

app = Flask(__name__)

TO_EMAIL = "kbre93@gmail.com"
FROM_EMAIL = "kieran.steps@gmail.com"

@app.route('/run_steps_history_updater', methods=['POST'])
def run_steps_history_updater(request=None): # Request arg needed for cloud, can't be a requirement for local run
    ''' Reads all unread emails in steps email
    Each new date, step count line to Firestore steps history
    '''
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    gmail_reader = GmailReader()
    firestore_service = FirestoreService()
    unread_email_list = gmail_reader.get_unread_emails()
    
    for id, unread_email in enumerate(unread_email_list):
        logger.info(f"Adding new steps history data to firestore ({id+1}/{len(unread_email_list)})")
        email_contents = gmail_reader.get_email_contents(unread_email['id'])
        steps_dict = parse_email_to_dict(email_contents)
        firestore_service.upload_dict(steps_dict, field_name='step_count')
        gmail_reader.mark_email_as_read(unread_email['id'])

    return "Steps history updated successfully"


@app.route('/run_steps_email_sender', methods=['POST'])
def run_steps_email_sender(request=None):
    ''' Reads step count history from Firestore, creates weekly summary fig
    Sends figure over email
    '''
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    firestore_service = FirestoreService()
    step_history_df = firestore_service.read_collection_to_dataframe()

    step_count_plotter = StepCountPlotter(step_history_df)
    fig_week_summary = step_count_plotter.plot_last_week_steps(display=False)

    email_sender = EmailSender(TO_EMAIL, FROM_EMAIL)
    email_sender.send_weekly_summary_email(fig_week_summary)

    return "Script executed successfully"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
