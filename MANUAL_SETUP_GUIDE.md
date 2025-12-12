# Manual Project Setup Guide

This guide provides step-by-step instructions for setting up and running the Verapath application directly with Python, without using Docker.

## 1. Prerequisites

*   **Python 3:** Ensure you have Python 3 installed on your machine.
*   **Git:** You will need Git to clone the repository.

## 2. Clone the Repository (if you haven't already)

If your friend hasn't already cloned the repository, they should do so first:

```bash
git clone <repository_url>
cd VeraPathTechnologies/VeraPathTechnologies
```
(Replace `<repository_url>` with the actual Git repository URL.)

## 3. Set up the Python Environment

It's highly recommended to use a virtual environment to manage project dependencies.

1.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    ```
2.  **Activate the virtual environment:**
    *   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```
    *   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```
3.  **Install dependencies:**
    Navigate to the `VeraPathTechnologies/VeraPathTechnologies` directory (the one containing `requirements.txt`) and run:
    ```bash
    pip install -r requirements.txt
    ```

## 4. Create the Environment File (`.env`)

The application requires an environment file to store secret keys and API credentials.

1.  Navigate to the `leakfix_mvp` directory:
    ```bash
    cd leakfix_mvp
    ```
2.  Create a new file named `.env` in this directory.
3.  Copy the following template into the file and fill in the values. **It is crucial to replace `your-super-secret-key-here` with a long, random string. You can use an online Django secret key generator.** You will also need to obtain the `ATHENA_CLIENT_ID` and `ATHENA_CLIENT_SECRET` from your Athena API setup.

    ```
    # Django Settings
    SECRET_KEY='your-super-secret-key-here'
    DEBUG=True
    DATABASE_URL='sqlite:///db.sqlite3' # Use SQLite for local development

    # Athena API Credentials
    # These are required for the application to connect to the Athena API.
    ATHENA_CLIENT_ID="YOUR_ATHENA_CLIENT_ID"
    ATHENA_CLIENT_SECRET="YOUR_ATHENA_CLIENT_SECRET"
    ```
4.  After creating the `.env` file, navigate back to the root of the Django project (`leakfix_mvp`'s parent directory, which contains `manage.py`):
    ```bash
    cd ..
    ```

## 5. Database Setup

1.  **Run migrations:**
    This command sets up the database schema.
    ```bash
    python leakfix_mvp/manage.py migrate
    ```

## 6. Populate Initial Data (from Athena)

This step imports essential data (Providers, Patients, Referrals) from the Athena API. You will need your `practice_id`, `client_id` (ATHENA_CLIENT_ID from your `.env`), and `client_secret` (ATHENA_CLIENT_SECRET from your `.env`).

```bash
python leakfix_mvp/manage.py import_athena --practice_id YOUR_ATHENA_PRACTICE_ID --client_id YOUR_ATHENA_CLIENT_ID --client_secret YOUR_ATHENA_CLIENT_SECRET
```
(Replace `YOUR_ATHENA_PRACTICE_ID`, `YOUR_ATHENA_CLIENT_ID`, and `YOUR_ATHENA_CLIENT_SECRET` with the actual values.)

## 7. Create a Superuser

To access the Django admin and dashboard, you need to create a superuser. Follow the prompts to set a username, email, and password.

```bash
python leakfix_mvp/manage.py createsuperuser
```

## 8. Run the Development Server

Finally, start the Django development server:

```bash
python leakfix_mvp/manage.py runserver
```

You should see output indicating the server has started, usually at `http://127.0.0.1:8000/`.

## 9. Access the Application

Open your web browser and navigate to `http://127.0.0.1:8000/`. You can log in with the superuser credentials you just created.

---
**Troubleshooting Tips:**
*   Ensure your virtual environment is always activated when running `python manage.py` commands.
*   Double-check your Athena API credentials and `practice_id` if you encounter API errors during data import.
*   If you face issues with the `SECRET_KEY`, try generating a new one (e.g., using an online Django secret key generator).