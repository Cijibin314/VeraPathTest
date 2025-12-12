# Shared Database Setup Guide

This guide explains how to switch from a local SQLite database to a shared, cloud-hosted PostgreSQL database. This will allow you and your friend to access the same data, so any changes made by one person (like creating a user) will be visible to the other.

## Why You Can't Share `db.sqlite3`

The `db.sqlite3` file is a file-based database that lives on your local machine. While it's great for individual development, it is not designed to be accessed by multiple computers over a network simultaneously. Trying to share it directly (e.g., via a shared folder) can lead to data corruption and other issues.

## The Solution: A Shared PostgreSQL Database

The best solution is to use a client-server database that both of you can connect to over the internet. We will use a free, cloud-hosted PostgreSQL database.

Here are the steps to set this up:

### 1. Install the PostgreSQL Driver

First, you and your friend need to install the necessary Python package to connect to a PostgreSQL database. I have already added the required package (`psycopg2-binary`) to your `requirements.txt` file.

Both of you should run the following command to install it (make sure your virtual environment is activated):

```bash
pip install -r requirements.txt
```

### 2. Create a Free Cloud-Hosted PostgreSQL Database

We'll use a service called [ElephantSQL](https://www.elephantsql.com/) which offers a free plan that is perfect for your needs.

1.  **Sign up for an account:** Go to the ElephantSQL website and create a free account.
2.  **Create a new instance:** Once you've signed up and logged in, create a new "instance."
    *   Give your instance a name (e.g., `verapath-dev`).
    *   Select the "Tiny Turtle" (free) plan.
    *   Choose a region that is closest to you.
3.  **Get the Database URL:** After the instance is created, go to the "Details" page for your new instance. You will see a "URL" that looks like this:
    ```
    postgres://username:password@hostname/databasename
    ```
    **This URL is your `DATABASE_URL`.** Copy it.

### 3. Update Your `.env` File

Now, both you and your friend need to update your `.env` files to point to the new shared database.

1.  Open the `.env` file located in the `leakfix_mvp` directory.
2.  Find the `DATABASE_URL` line and replace it with the URL you copied from ElephantSQL.

Your `.env` file should now look something like this:

```
# Django Settings
SECRET_KEY='your-super-secret-key-here'
DEBUG=True
DATABASE_URL='postgres://username:password@hostname/databasename' # From ElephantSQL

# Athena API Credentials
ATHENA_CLIENT_ID="YOUR_ATHENA_CLIENT_ID"
ATHENA_CLIENT_SECRET="YOUR_ATHENA_CLIENT_SECRET"
```

### 4. Run Migrations on the New Database

Since this is a brand new, empty database, you need to set up the tables. **Only one of you needs to do this.**

Run the migrate command, pointing to your new database (make sure the `DATABASE_URL` in your `.env` file is the new PostgreSQL one):
```bash
python leakfix_mvp/manage.py migrate
```

### 5. Choose How to Populate the Shared Database

You have two options: you can either migrate the data from your existing local `db.sqlite3` file, or you can start with a fresh, empty database and re-populate it from the Athena API.

---

### Option A: Migrate Your Existing Local Data (Recommended)

Follow these steps if you want to preserve the data (users, referrals, etc.) that is currently in your local `db.sqlite3` database.

**This process should be done by the person who has the data to migrate.**

**Step 1: Export your local data**

First, temporarily switch your `.env` file back to point to your local SQLite database:
```
# In leakfix_mvp/.env
DATABASE_URL='sqlite:///db.sqlite3'
```

Now, run the `dumpdata` command to export all your data into a single file named `datadump.json`. This file will be created in the root of the project.

```bash
python leakfix_mvp/manage.py dumpdata > datadump.json
```
**Note:** This can take a moment and the file can be large if you have a lot of data.

**Step 2: Switch back to the new PostgreSQL database**

Update your `.env` file again to point back to your new shared PostgreSQL database from ElephantSQL:
```
# In leakfix_mvp/.env
DATABASE_URL='postgres://username:password@hostname/databasename'
```

**Step 3: Import your data**

Now, run the `loaddata` command to import the data from `datadump.json` into the new shared database.

```bash
python leakfix_mvp/manage.py loaddata datadump.json
```

Your existing data has now been migrated! You can now proceed to the "You're All Set!" section.

---

### Option B: Start with a Fresh Database

Follow these steps if you don't need to preserve any local data and want to start fresh.

**Only one of you needs to do this.**

Run the import and user creation commands:

```bash
# Import data from Athena
python leakfix_mvp/manage.py import_athena --practice_id YOUR_ATHENA_PRACTICE_ID --client_id YOUR_ATHENA_CLIENT_ID --client_secret YOUR_ATHENA_CLIENT_SECRET

# Create a superuser (you can create one for each of you)
python leakfix_mvp/manage.py createsuperuser
```
---

## You're All Set!

Now, when you and your friend run the server (`python leakfix_mvp/manage.py runserver`), you will both be connected to the same database. Any user created, any data imported, and any changes made will be reflected for both of you.
