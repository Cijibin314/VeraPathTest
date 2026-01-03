# Verapath Project Setup with Docker

This guide will walk you through setting up and running the Verapath application using Docker. With this method, you do not need to install Python, Pip, or any other system dependencies on your host machine.

## Prerequisites

1.  **Git:** To clone the repository.
2.  **Docker & Docker Compose:** To build and run the application container. [Install Docker](https://docs.docker.com/get-docker/).

---

## Setup Steps

### 1. Clone the Repository

First, clone the project repository to your local machine and navigate into the project directory.

```bash
git clone <your-repository-url>
cd VeraPathTechnologies
```

### 2. Create the Environment File

The application requires an environment file (`.env`) to store secrets like the database URL and other configuration variables.

1.  Create a new file named `.env` inside the `leakfix_mvp/` directory.
2.  Copy and paste the following content into the file.

    ```
    # leakfix_mvp/.env

    # ------------------- DATABASE -------------------
    # PostgreSQL connection URL for the shared development database.
    DATABASE_URL=""

    # ------------------- DJANGO -------------------
    # A secret key for this Django installation.
    SECRET_KEY=""
    DEBUG=True

    # ------------------- ATHENA API -------------------
    # AthenaNet API Credentials
    ATHENA_CLIENT_ID=""
    ATHENA_CLIENT_SECRET=""
    ```

3.  Replace `<PASTE_YOUR_DATABASE_URL_HERE>` with the actual Neon database URL shared with the development team.

### 3. Build and Run the Application

Now, you can build the Docker image and start the application using a single command from the project's root directory (where `docker-compose.yml` is located).

```bash
docker compose up --build
```

> **Note for Linux Users:** If you get a "permission denied" error, you may need to run the command with `sudo`:
> ```bash
> sudo docker compose up --build
> ```
> To avoid using `sudo` every time, you can add your user to the `docker` group. (See Docker's official post-installation steps for Linux).

This command will:
- Build the Docker image from the `Dockerfile`.
- Start the container.
- Automatically run database migrations.
- Start the Gunicorn web server.

### 4. Access the Application

Once the server is running, open your web browser and navigate to:
**http://localhost:8000/analytics/dashboard/**

### 5. Stopping the Application

To stop the running application, go to the terminal where `docker-compose` is running and press `Ctrl+C`.

---

## Additional Docker Commands

To run Django management commands (like `createsuperuser`), you can execute them in the running container.

First, start the application with `docker-compose up`. Then, in a **new terminal window**, use the `docker-compose exec` command:

```bash
# Example: Create a new superuser
docker-compose exec web python manage.py createsuperuser

# General format
docker-compose exec web python manage.py <your-command-here>
```
