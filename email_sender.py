from firestore_service import FirestoreService
from step_summary_plotter import StepSummaryPlotter
from step_history_processor import StepHistoryProcessor
import matplotlib.pyplot as plt
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import io
import logging
import os
from dotenv import load_dotenv

TO_EMAIL = "kbre93@gmail.com"
FROM_EMAIL = "kieran.steps@gmail.com"

class EmailSender:

    def __init__(self, to_email, from_email):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        self.to_email = to_email
        self.from_email = from_email

        load_dotenv()
        self.from_email_pass = os.environ.get('GMAIL_APP_PASSWORD')
        
        if not self.from_email_pass:
            self.logger.error("GMAIL_APP_PASSWORD environment variable is not set")
            raise ValueError("Email password not found in environment variables")

    def _create_dummy_fig(self):
        ''' Returns a bytes buffer of a figure for a dummy image
        '''
        # Create a simple plot
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        plt.figure()
        plt.plot(x, y)
        plt.title("Sine Wave")
        plt.xlabel("X")
        plt.ylabel("Y")

        # Save the plot to a bytes buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        
        return buffer
    
    def _create_bytes_buffer_from_fig(self, fig):
        """
        Convert a matplotlib figure to a bytes buffer.
        fig: matplotlib figure object. Returns io.BytesIO object containing the figure in PNG format
        """
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        plt.close(fig)
        return buffer

    def _build_MIMEMultipart_with_image(self, subject, message_text, image_buffer):
        ''' Returns a MIMEMultipart object with headers, HTML content, and and embeed image
        image_buffer is a bytes buffer
        '''
        # Create the email
        msg = MIMEMultipart('related')
        msg['From'] = self.from_email
        msg['To'] = self.to_email
        msg['Subject'] = subject

        # Create the HTML part of the email
        html = f"""
        <html>
        <body>
            <p>{message_text}</p>
            <img src="cid:image1">
        </body>
        </html>
        """

        # Attach the HTML part
        msg.attach(MIMEText(html, 'html'))

        # Attach the image to the email
        image = MIMEImage(image_buffer.getvalue())
        image.add_header('Content-ID', '<image1>')
        msg.attach(image)

        return msg

    def _send_email(self, msg):
        ''' Sends an email
        msg is a MIMEMultipart object (with headers, HTML content, embedded image)
        '''
        # Send the email
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = self.from_email
        smtp_password = self.from_email_pass

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        self.logger.info("Email sent successfully!")

    def send_dummy_email(self):
        ''' Sends a dummy email with a dummy figure
        '''
        subject = 'Dummy email'
        message_text = 'This is a test email'

        try:
            dummy_fig_bytes_buffer = self._create_dummy_fig()
        except Exception as e:
            self.logger.error(f"Failed to create dummy figure: {str(e)}")
            return
        try:
            email_msg = self._build_MIMEMultipart_with_image(subject, message_text, dummy_fig_bytes_buffer)
        except Exception as e:
            self.logger.error(f"Failed to build email: {str(e)}")
            return
        try:
            self._send_email(email_msg)
        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            return
        
    def send_weekly_summary_email(self, fig):
        ''' Sends a weekly summary email
        '''
        subject = 'Your weekly step summary'
        message_text = ''

        try:
            fig_bytes_buffer = self._create_bytes_buffer_from_fig(fig)
        except Exception as e:
            self.logger.error(f"Failed to create dummy figure: {str(e)}")
            return
        try:
            email_msg = self._build_MIMEMultipart_with_image(subject, message_text, fig_bytes_buffer)
        except Exception as e:
            self.logger.error(f"Failed to build email: {str(e)}")
            return
        try:
            self._send_email(email_msg)
        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            return

if __name__ == "__main__":
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    firestore_service = FirestoreService()
    step_history_df = firestore_service.read_collection_to_dataframe()

    step_count_plotter = StepSummaryPlotter(step_history_df)

    step_history_processor = StepHistoryProcessor(step_history_df)

    step_count_plotter = StepSummaryPlotter(step_history_processor)
    fig = step_count_plotter.create_summary_plot()

    email_sender = EmailSender(TO_EMAIL, FROM_EMAIL)
    # email_sender.send_dummy_email()
    email_sender.send_weekly_summary_email(fig)

