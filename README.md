# Bank Term Deposit Prediction With Django

A Django-based machine learning web application that predicts whether a customer is likely to subscribe to a **bank term deposit** based on banking campaign data.  
The project also includes **Single Sign-On (SSO)** using **Keycloak** with **OpenID Connect (OIDC)** for secure authentication.

---

## Overview

This project is built to help predict customer subscription outcomes for a bank term deposit campaign.  
Users authenticate through **Keycloak SSO**, upload a CSV file containing customer records, and receive prediction results as a downloadable CSV.

The application combines:

- Django web framework
- Machine learning inference using a saved Joblib model
- CSV batch prediction workflow
- Preprocessing pipeline for categorical and boolean features
- Keycloak-based OIDC authentication

---

## Features

### Machine Learning Features
- Batch prediction using uploaded CSV files
- Automatic preprocessing before inference
- Encodes categorical columns using one-hot encoding
- Converts boolean values like `yes/no` into numeric format
- Returns prediction output as downloadable CSV
- Predicts whether the customer will subscribe to a term deposit

### Authentication Features
- Login with Keycloak SSO
- OIDC integration using `mozilla-django-oidc`
- Registration flow through Keycloak
- Protected prediction page using Django authentication
- Session-based login/logout support

### User Features
- Home page / landing page
- Secure login flow
- CSV upload for predictions
- Downloadable prediction results file

---

## Tech Stack

**Backend**
- Python
- Django

**Machine Learning**
- scikit-learn
- Joblib
- pandas

**Authentication**
- Keycloak
- OpenID Connect (OIDC)
- mozilla-django-oidc

**Database**
- SQLite

**Frontend**
- HTML
- Django Templates

---

## Project Structure

```bash
Bank_Term_Deposit_Prediction_With_Django/
│
├── predictor/                    # Main app for prediction logic
├── templates/                    # HTML templates
├── term_deposit_project/         # Django project settings and URLs
├── db.sqlite3                    # SQLite database
├── manage.py                     # Django management script
└── requirements.txt              # Project dependencies
```

## How It Works

### 1. Authentication
The user accesses the application and logs in through **Keycloak SSO** using **OIDC**.

- Django redirects the user to Keycloak
- Keycloak authenticates the user
- The user is redirected back to Django through the callback endpoint
- Django starts a session for the authenticated user

### 2. CSV Upload
After login, the user uploads a CSV file containing customer data.

**Expected workflow:**
- Read CSV file using `pandas`
- Drop the target column `y` if present
- Preprocess the data
- Load the trained model from Joblib
- Generate predictions

### 3. Prediction Output
The system:

- predicts **Yes** or **No**
- appends predictions to the uploaded data
- returns a downloadable CSV file named `predictions.csv`

---

## Preprocessing Logic

Before prediction, the app applies preprocessing to uploaded data.

### Categorical Columns
These columns are one-hot encoded:

- `job`
- `marital`
- `education`
- `contact`
- `month`
- `poutcome`

### Boolean Columns
These columns are converted into numeric values:

- `housing`
- `loan`

**Example mapping:**
- `yes` → `1`
- `no` → `0`

The processed dataframe is then aligned to the exact feature columns expected by the trained model.

---

## Model Input

The uploaded CSV should include columns relevant to the trained model.

Some example columns may include:

- `age`
- `job`
- `marital`
- `education`
- `default`
- `balance`
- `housing`
- `loan`
- `contact`
- `day`
- `month`
- `duration`
- `campaign`
- `pdays`
- `previous`
- `poutcome`

If the uploaded file contains a target column named `y`, it is automatically removed before inference.

---

## Prediction Output

The model returns predictions in this format:

- **Yes** → Customer is likely to subscribe
- **No** → Customer is not likely to subscribe

The output CSV adds a new column:

Prediction

## OIDC / Keycloak Integration

This project uses **Keycloak** as the identity provider and **mozilla-django-oidc** for OIDC authentication in Django.

### Current OIDC Setup
The settings include:

- Keycloak server URL
- Realm name
- Client ID
- Client secret
- Authorization endpoint
- Token endpoint
- User info endpoint
- JWKS endpoint
- Logout endpoint

---

## Running Keycloak Locally with Docker

You can run Keycloak locally using Docker:

```bash
docker run -d --name keycloak ^
  -p 8080:8080 ^
  -e KC_BOOTSTRAP_ADMIN_USERNAME=admin ^
  -e KC_BOOTSTRAP_ADMIN_PASSWORD=admin123 ^
  quay.io/keycloak/keycloak:latest ^
  start-dev
```

**Open Keycloak Admin Console**
```bash
http://localhost:8080
```
**Example Keycloak Configuration** 

Create:

* Realm: sso-demo
* Client: app3-bank-client

Example Redirect URIs
```bash
http://127.0.0.1:8002/oidc/callback/
http://localhost:8002/oidc/callback/
```
Example Post Logout Redirect URIs
```bash

http://127.0.0.1:8002/
http://localhost:8002/
```
Local Setup
1. Clone the Repository
```bash
git clone https://github.com/Friendlysiva143/Bank_Term_Deposit_Prediction_With_Django.git
cd Bank_Term_Deposit_Prediction_With_Django
```
2. Create Virtual Environment
```bash
python -m venv venv
```
3. Activate Virtual Environment

Windows
```bash
venv\Scripts\activate
```
Linux / Mac

source venv/bin/activate

4. Install Dependencies
```bash
pip install -r requirements.txt
5. Run Migrations
```bash
python manage.py migrate
```
6. Run the Django Server
```bash
python manage.py runserver
```

Open in browser:
```bash
http://127.0.0.1:8002/

```
Model File Requirement

This project expects the trained model file at:
```bash
predictor/model/term_deposit_prediction_model.joblib
```
If the model file is missing, the app returns:
```bash
Model file not found. Please train the model first.
```

### Main Functional Flow
* User opens the application
* User logs in using Keycloak SSO
* User uploads a CSV file
* Django loads the trained Joblib model
* Uploaded data is preprocessed
* Predictions are generated
* Output CSV is returned for download

### Routes Overview

Typical routes in the project include:

* / → home page
* protected prediction page handled by Django view
* /oidc/authenticate/ → login via OIDC
* /oidc/callback/ → OIDC callback
* custom register flow through Keycloak registration action
* logout route returning user to home page

### Security Note

The current settings file includes hardcoded development values for:

* Django secret key
* Keycloak client secret
* Keycloak server URL

For production use, move all sensitive settings into environment variables and use HTTPS.

Recommended environment variables:

* SECRET_KEY
* DEBUG
* ALLOWED_HOSTS
* KEYCLOAK_SERVER_URL
* KEYCLOAK_REALM
* OIDC_RP_CLIENT_ID
* OIDC_RP_CLIENT_SECRET

### Future Improvements
* Add single-record prediction form
* Add model confidence score display
* Improve UI styling and dashboard
* Move secrets to .env
* Deploy Keycloak publicly for production
* Add PostgreSQL for production use
* Add prediction history tracking
* Add model evaluation metrics section

**Author**

Siva Prasad

GitHub: https://github.com/sivaprasadkandena/

**License**

This project is for learning, academic, and portfolio purposes.