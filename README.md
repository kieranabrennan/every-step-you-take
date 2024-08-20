## Set up Shortcuts on iPhone


## Set up Google Cloud platform
- Enable Gmail API
- Enable OAuth consent screen
- Create Credentials for OAuth 2.0, download .json

- Program authenticates through OAuth screen once. Stores token in Google Storage bucket
- Subsequent authentication accesses this bucket, to refresh the token

## Set up Firestore
- Enable API on project
- Create service account, give roles for Firestore
    - Requires Cloud Datastore User, Firebase Admin SDK Administrator Service Agent, 
    Firebase Rules System, Firestore Service Agent, Cloud Storage for Firebase Admin
- Create .json key and download

- Create a Firestore database
- Leave name as (default)

## Set up Email sender
- In Gmail, setup an app password, password. 2FA needs to be enabled, then create at https://myaccount.google.com/apppasswords



- Run locally once to set up the gmail authentication token. This is then stored in the bucket


gcloud functions deploy YOUR_FUNCTION_NAME \
  --set-env-vars EMAIL_PASSWORD="$(grep EMAIL_PASSWORD .env | cut -d '=' -f2)" \
  ... (other deployment options)