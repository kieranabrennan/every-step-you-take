## Set up Shortcuts on iPhone


## Set up Google Cloud platform
- Enable Gmail API
- Enable OAuth consent screen
- Create Credentials for OAuth 2.0, download .json

- Program authenticates through OAuth screen once. Stores token in Google Storage bucket
- Subsequent authentication accesses this bucket, to refresh the token

## Set up Firestore
- Enable API in Google cloud project
- Create service account, give roles for Firestore
    - Requires Cloud Datastore User, Firebase Admin SDK Administrator Service Agent, 
    Firebase Rules System, Firestore Service Agent, Cloud Storage for Firebase Admin
- Create .json key and download

- Create a Firestore database
  - Leave name as (default)

## Set up Email sender
- In Gmail, setup an app password, password. 2FA needs to be enabled, then create at https://myaccount.google.com/apppasswords
- Create a .env and add as GMAIL_APP_PASSWORD="app password"


## Cloud functions
- Enable Cloud Functions, Cloud Build, Cloud Run

- Run locally once to set up the gmail authentication token. This is then stored in the bucket

Userful gcloud functions, handling accounts and projects
- Check login with `glcoud auth list`
- Change account with `gcloud config set account email_address`
- Check the project with `gcloud config get-value project`
- Change the project with `gcloud config set project YOUR-PROJECT-ID`
- List all service accounts in project `gcloud iam service-accounts list`
- Default service account should be: [PROJECT-ID]@appspot.gserviceaccount.com
- Ensure default service account has necessary permissions 

## Running locally
- To have this working locally add with .env with:
RUNNING_LOCALLY=True

- Run `python3 main.py` to start the flask server

#### Steps History Updater
`curl -X POST http://localhost:8080/run_steps_history_updater`

#### Steps Email Sender
`curl -X POST http://localhost:8080/run_steps_email_sender`

### Pushing as a cloud function
```
gcloud projects add-iam-policy-binding kieran-steps \
  --member="serviceAccount:kieran-steps@appspot.gserviceaccount.com" \
  --role="roles/cloudfunctions.developer"
```
```
gcloud projects add-iam-policy-binding kieran-steps \
  --member="serviceAccount:kieran-steps@appspot.gserviceaccount.com" \
  --role="roles/cloudfunctions.invoker"
```
- Create cloud function with:
```
gcloud functions deploy run_steps_history_updater \
    --gen2 \
    --entry-point run_steps_history_updater \
    --runtime python39 \
    --trigger-http \
    --allow-unauthenticated \
    --memory 512MB \
    --timeout 540s \
    --region us-central1
```

```
gcloud functions deploy run_steps_email_sender \
    --gen2 \
    --entry-point run_steps_email_sender \
    --runtime python39 \
    --trigger-http \
    --allow-unauthenticated \
    --memory 512MB \
    --timeout 540s \
    --region us-central1 \
    --set-env-vars GMAIL_APP_PASSWORD="$(sed -n 's/^GMAIL_APP_PASSWORD="\(.*\)"/\1/p' .env)"
```
- Run with
```
gcloud functions call run_steps_history_updater --region us-central1
```

```
gcloud functions call run_steps_email_sender --region us-central1
```