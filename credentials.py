
from dotenv import load_dotenv
import os

GOOGLE_SA_CRED_FILEPATH = "./google_service_account_credentials.json"

def set_credentials_env_var():
    ''' Sets Google Application credentials for Firestore, gmail
    When running as a cloud function, env-var is not set as this is handled by the associated service account
    Note: To work locally, must Create a .env with RUNNING_LOCALLY=True, and have service account credentials json
    with appropriate permissions at the path above.
    '''
    load_dotenv()
    running_locally = os.getenv('RUNNING_LOCALLY', 'False').lower() == 'true'
    if running_locally:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_SA_CRED_FILEPATH
    else:
        pass # Credentials are handled when deployed as cloud function