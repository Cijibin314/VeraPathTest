# Verapath Project Documentation

This document provides an overview of the Verapath project's codebase, structure, and functionality.

## Operational Guidelines

- **Never run the development server.** Always ask the user to start it.

## Project Overview

The Verapath project is a Django-based web application designed for analytics of referral leakage in a healthcare context. It helps track patient referrals, identify out-of-network referrals, and analyze the associated costs and revenue. The application provides a dashboard with key performance indicators (KPIs), detailed views of referrals and providers, and an invoicing system.

## Technology Stack

- **Backend:** Python with the Django framework.
- **Database:** PostgreSQL in production (as inferred from `environ` usage), with SQLite for development.
- **Frontend:** Django templates with HTML, and likely some CSS/JavaScript (though not explicitly reviewed yet).
- **Environment Configuration:** `python-environ` is used to manage settings via a `.env` file.

## Codebase Structure

The project is organized as a standard Django project with a single application:

- **`leakfix_mvp/`**: The root directory of the Django project.
  - **`manage.py`**: The Django command-line utility.
  - **`leakfix/`**: The main project configuration directory.
    - **`settings.py`**: Contains the project settings, including database configuration, installed apps, and middleware.
    - **`urls.py`**: The main URL routing file, which includes the URLs from the `analytics` app.
  - **`analytics/`**: A Django app that contains the core functionality of the application.
    - **`models.py`**: Defines the database schema with models such as `Patient`, `Provider`, `Referral`, and `Invoice`.
    - **`views.py`**: Contains the business logic for handling web requests and rendering templates. This includes the main dashboard, referral details, and other pages.
    - **`urls.py`**: Defines the URL patterns for the `analytics` app.
    - **`templates/`**: Contains the HTML templates for the `analytics` app.
  - **`templates/`**: A global directory for templates.

## How it Works

The application revolves around the concept of a **Referral**. A referral is created when a patient is referred to a provider. The application tracks the status of the referral, whether it is in-network or out-of-network, and the associated costs.

### Key Models:

- **`Patient`**: Represents a patient. The patient's ID is pseudonymized to protect privacy.
- **`Provider`**: Represents a healthcare provider, with details like NPI, name, and specialty.
- **`Payer`**: Represents an insurance payer.
- **`Referral`**: The central model that connects a patient, provider, and payer. It tracks the status, cost, and other details of the referral.
- **`Invoice`**: Used for generating invoices based on retained revenue from in-network referrals.

### Key Views:

- **`dashboard`**: The main landing page, which displays a variety of KPIs, such as:
  - Total number of referrals.
  - In-network vs. out-of-network referrals.
  - Referral leakage cost.
  - Completion rates and times.
- **`referral_detail`**: Shows the details of a specific referral and suggests alternative in-network providers.
- **`specialty_dashboard`**: Provides a breakdown of metrics by provider specialty.
- **`metric_detail`**: Shows historical data for a specific metric and provides AI-generated suggestions for improvement.

## Key Features

- **KPI Dashboard**: A comprehensive overview of referral analytics.
- **Referral Tracking**: Detailed tracking of each referral's lifecycle.
- **Provider Suggestion Engine**: Suggests alternative in-network providers to reduce leakage.
- **Cost and Revenue Analysis**: Calculates leakage costs and retained revenue.
- **Invoicing**: Generates invoices based on performance.
- **Data-driven Insights**: Provides insights into referral patterns by specialty and payer.