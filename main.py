import logging
from flask import Flask
from firestore_service import FirestoreService
from step_count_plotter import StepCountPlotter
from email_sender import EmailSender
from gmail_reader import GmailReader
from gmail_to_firestore import parse_email_to_dict
import os

app = Flask(__name__)

@app.route('/run_steps_history_update', methods=['POST'])
def run_steps_history_update(request=None):
    gmail_reader = GmailReader()
    firestore_service = FirestoreService()
    unread_email_list = gmail_reader.get_unread_emails()
    
    for unread_email in unread_email_list:
        email_contents = gmail_reader.get_email_contents(unread_email['id'])
        steps_dict = parse_email_to_dict(email_contents)
        
        firestore_service.upload_dict(steps_dict, field_name='step_count')
        gmail_reader.mark_email_as_read(unread_email['id'])

    return "Steps history updated successfully", 200


@app.route('/run_steps_email_sender', methods=['POST'])
def run_steps_email_sender(request=None):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    firestore_service = FirestoreService()
    step_history_df = firestore_service.read_collection_to_dataframe()

    step_count_plotter = StepCountPlotter(step_history_df)
    fig_week_summary = step_count_plotter.plot_last_week_steps(display=False)

    to_email = "kbre93@gmail.com"
    from_email = "kieran.steps@gmail.com"

    email_sender = EmailSender(to_email, from_email)
    email_sender.send_weekly_summary_email(fig_week_summary)

    return "Script executed successfully"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
