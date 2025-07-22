# ⚖️ Judgement Case Management System

A robust Django-based web application designed to help legal professionals manage court cases, transactions, and payoff statements. The system allows users to securely track judgment amounts, apply interest rates, log payments and costs, generate PDF summaries, and manage their profile and subscription plans.

----------

## 🚀 Features

-   **User Authentication**
    
    -   Secure login & registration
        
    -   Profile view and update
        
    -   JWT-based authentication
        
-   **Case Management**
    
    -   Create, view, update, and soft-delete legal cases
        
    -   Track court info, judgment amount, interest rates, and dates
        
    -   Filter and search your own cases
        
-   **Transaction Management**
    
    -   Add, view, and delete case-specific transactions
        
    -   Supports transaction types: `PAYMENT`, `COST`, `INTEREST`
        
    -   Real-time calculation of new balances and interest
        
-   **PDF Generation**
    
    -   Generate beautifully formatted **Payoff Statement PDFs**
        
    -   Export full **Transaction Histories** as PDF (filtered by date)
        
    -   Powered by `xhtml2pdf` for server-side rendering
        
-   **Subscription Handling**
    
    -   Track plan status (`free`, `paid`) and account activity
        
    -   Display plan info on profile
        

----------

## 🧰 Tech Stack

| Layer          | Tech                                        |
| -------------- | ------------------------------------------- |
| Backend        | Django, Django REST Framework               |
| PDF Generation | `xhtml2pdf`, Django Templates               |
| Auth           | JWT (SimpleJWT)                             |
| Database       | PostgreSQL / SQLite3                        |
| API Client     | Postman (for development)                   |
| Deployment     | Vercel (Frontend), Railway/Render (Backend) |


----------

## 📂 Folder Structure

```bash
judgement_portal/
├── authentication/       # Handles user login, registration, profile
├── docket/               # Manages cases and transactions
├── judgement_portal/     # Project Directory
├── manage.py
└── requirements.txt

```

----------

## 📦 Setup Instructions

### 1. Clone the Repo

```bash
git clone https://github.com/Abdul-Ikram/Judgement-Calculator.git
cd Judgement-Calculator

```

### 2. Create Virtual Environment & Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # For Windows: .venv\Scripts\activate
pip install -r requirements.txt

```

### 3. Set Up `.env`

Create a `.env` file with:

```env
# Looking to send emails in production? Check out our Email API/SMTP product!
EMAIL_BACKEND = ''
EMAIL_USE_TLS = 
EMAIL_USE_SSL = 
EMAIL_PORT = 
EMAIL_HOST = ''
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
DEFAULT_FROM_EMAIL = ''

# API key used to authenticate requests to ImageKit (image storage service)
IMAGEKIT_API_KEY = ''

# PostgreSQL connection string for NeonDB cloud database (used by dj_database_url)
# Format example: postgres://username:password@host:port/database
psql = ''


```

### 4. Run Migrations & Create Superuser

```bash
python manage.py makemigrations
python manage.py migrate

```

### 5. Run the Server

```bash
python manage.py runserver

```

----------

## 🧪 API Testing (via Postman)

Base URL (Local):

```
http://127.0.0.1:8000/

```

Example Endpoints:

-   `POST /auth/login/`

-   `POST /docket/api/cases/`
    
-   `GET /docket/api/cases/<case_id>/payoff-statement/?date=YYYY-MM-DD`
    
-   `GET /docket/api/cases/<case_id>/transactions/download/?date=YYYY-MM-DD`
    

> ✅ All endpoints are secured. Use the JWT `Authorization: Bearer <token>` header.

----------

## 📄 Sample PDF Output

The application dynamically generates PDFs using Django Templates and `xhtml2pdf`. Below are sample documents:

-   **Payoff Statement**
    
    -   Shows total due with interest as of selected date.
        
    -   Stylish layout with lawyer and recipient info.
        
-   **Transaction History**
    
    -   Lists all case transactions up to specified date.
        
    -   Includes interest, balances, and description.
        

----------

## 👤 Maintained By

**Abdul Ikram**  
For business inquiries, legal tech projects, or freelance collaboration, feel free to connect.

----------

## 🛡️ License ![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

This project is licensed under the [MIT License](https://github.com/Abdul-Ikram/Judgement-Calculator/tree/main/LICENSE).

----------

## 🙌 Acknowledgements

-   Django & DRF community
    
-   PythonAnywhere/Vercel/Render for deployment support
    
-   Fellow collaborators & testers who helped polish the system
    

----------