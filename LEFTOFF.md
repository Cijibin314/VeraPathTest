# Project Status and Next Steps

This document summarizes the investigation into connecting the application to the Athenahealth API and outlines the current status.

## Goal

The primary goal was to import live data from the Athenahealth API into the application's database using one of the existing management commands.

## Investigation Summary

We attempted to use the `import_athena.py` command, which led to a series of debugging steps:

1.  **`NameResolutionError`**: We first discovered the script was using an incorrect hostname (`api.athenahealth.com`). We corrected this to `api.preview.platform.athenahealth.com`.

2.  **`400 Bad Request` / `Invalid Scope`**: After fixing the hostname, we found that the API requires an explicit `scope` parameter in the token request. 

3.  **`403 Forbidden` / `Invalid Access Token`**: We began testing various `system/` scopes (e.g., `system/CarePlan.read`, `system/Patient.read`, `system/Practitioner.read`). While the authentication server granted tokens for these scopes, the FHIR API server consistently rejected them with `403 Forbidden` or related errors.

4.  **Practice ID Verification**: We tested all three documented test `practiceId`s (`80000`, `195900`, `1128700`) and confirmed the `403 Forbidden` error occurred with all of them.

5.  **Automated Testing**: We created the `test_api_access.py` script to create a repeatable, automated test case. This script successfully confirmed the core issue: we can get a token, but that token is forbidden from accessing the corresponding API resource.

## Current Understanding & Conclusion

We have definitively concluded that there is a **server-side configuration issue** with the API client account.

- The Athenahealth authentication server and their FHIR API server are not in agreement about the client's permissions.
- The authentication server correctly issues tokens for FHIR scopes.
- The FHIR server incorrectly rejects these valid tokens with a `403 Forbidden` error.

This problem **cannot be solved by modifying our code**. It is an issue with the permissions and policies associated with the API client on the Athenahealth platform.

## Blockers & Available Next Steps

- **API Import is Blocked**: We cannot proceed with importing any data from the live API until the server-side permission issue is resolved by the API provider.

- **Local Import is Available**: The only viable path to populate the application with data is to use the local import method. This involves:
    1. Creating a `sample_referrals.csv` file.
    2. Using the `python manage.py import_referrals` command to load the data from that file.
