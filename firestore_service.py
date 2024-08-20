import logging
import os
from google.cloud import firestore
from datetime import datetime
import pandas as pd

DB_COLLECTION_NAME = "step_history"

class FirestoreService:

    def __init__(self):
        if not os.getenv('FUNCTION_NAME'):
            # This means the code is not running in a Google Cloud Function
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "./google_service_account_credentials.json"
        
        self.db = firestore.Client()

    def upload_dict(self, my_dict, field_name='value'):
        '''
        Uploads a dictionary where key is the document and value is uploaded under field_name
        '''    
        collection_ref = self.db.collection(DB_COLLECTION_NAME)
        for key, value in my_dict.items():
            doc_ref = collection_ref.document(key) 
            doc_ref.set({field_name: value})
    
    def read_collection_to_dataframe(self):
        '''
        Reads the step_history collection and outputs to dataframe
        Columns of date and step_count
        '''        

        docs = self.db.collection(DB_COLLECTION_NAME).stream()
        data = []

        # Loop through each document and extract data
        for doc in docs:
            doc_dict = doc.to_dict()
            # Assuming doc.id is the date in 'YYYY-MM-DD' format
            date_str = doc.id
            # Convert the date string to a datetime object
            date = datetime.strptime(date_str, '%Y-%m-%d')
            # Extract the step_count value and ensure it's an integer
            step_count = int(doc_dict.get('step_count', 0))
            # Append the data to the list
            data.append({'date': date, 'step_count': step_count})

        # Convert the list of dictionaries to a DataFrame
        df = pd.DataFrame(data)

        # Ensure the date column is a datetime type
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date', ascending=True)

        return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    firestore_service = FirestoreService()
    df = firestore_service.read_collection_to_dataframe()

    print(df)
    