# Part One Summary: Smart In-Network Directory

This report summarizes the progress made on the "Smart In-Network Directory" feature, comparing the planned tasks with the actual implementation and noting any deviations or limitations.

## 1) Smart In-Network Directory - Providers Tab Enhancements

### Provider Profiles:
- **specialty/subspecialty:** **Achieved.** The `import_provider_data.py` script was updated to fetch and store provider specialties and subspecialties from the Athenahealth API.
- **locations (city, state):** **Achieved.** The `import_provider_data.py` script was enhanced to retrieve the `usualdepartmentid` for each provider and then query the `/departments` endpoint to populate the `city` and `state` fields.
- **NPI (practice id):** **Achieved.** This field was already being imported and used as the unique identifier for providers.
- **insurances accepted:** **Not Achieved (API Limitation).** The Athenahealth API, as accessed through the sandbox environment, does not provide data for accepted insurance plans. Consequently, the `insurances_accepted` field was removed from the `Provider` model and related code.
- **hospital affiliations:** **Not Achieved (API Limitation).** The Athenahealth API does not directly provide comprehensive hospital affiliation data. While an attempt was made to infer affiliations from `ishospitaldepartment` flags in department data, the field was ultimately removed from the `Provider` model due to lack of reliable API data.
- **new-patient status:** **Achieved.** The `import_provider_data.py` script was updated to fetch and store the `acceptingnewpatients` status from the Athenahealth API.
- **average wait time:** **Not Achieved (API Limitation).** The Athenahealth API does not provide data for average wait times. Consequently, the `average_wait_time` field was removed from the `Provider` model and related code.
- **Primary Department:** **Achieved.** A `primary_department` field was added to the `Provider` model and populated by the `import_provider_data.py` script using the department name associated with the provider's `usualdepartmentid`. This is displayed on the dashboard.

### Network Rules Engine: Mark "Preferred" Providers
- **ACO contract (explicit in-network providers):** **Achieved.** Logic was implemented in the `provider_list` and `provider_search` views to mark providers as preferred if their `full_name` matches entries in the `in-network_providers` list from `ACO.txt`.
- **Geography:** **Achieved.** Logic was implemented in the `provider_list` and `provider_search` views to mark providers as preferred if their `city` and `state` match the `location` specified in `ACO.txt`.
- **Payer:** **Not Achieved (API Limitation).** While the `ACO.txt` file was updated to include `preferred_payers` and the logic to check against `provider.insurances_accepted` was in place, this rule cannot be fully applied with real data due to the API's lack of `insurances_accepted` information. The rule will currently not mark providers as preferred based on payer data.
- **Service Line:** **Disregarded.** The user decided to disregard this criterion for marking preferred providers.
- **Dynamic Sorting and Visual Indicator:** **Achieved.** Providers are now sorted with preferred providers appearing first, and a "⭐" icon visually indicates their preferred status.

### Search & Filters:
- **Search by name, specialty, subspecialty, city, state, primary_department:** **Achieved.** An AJAX-based search functionality was implemented, allowing real-time filtering of providers by these fields.
- **proximity, availability window, language, telehealth, pediatric/adult:** **Not Implemented (API Limitations/Scope).** These filtering options were not implemented due to the unavailability of the necessary data from the Athenahealth API or being outside the current scope of work.

## Summary of API Limitations Encountered:
- The Athenahealth API (via the sandbox environment and current endpoints) does not provide:
    - Detailed accepted insurance plans for providers.
    - Comprehensive hospital affiliations for providers.
    - Average wait times for providers.
    - Granular referral lifecycle timestamps (e.g., `completed_at`, `scheduled_at`, `acknowledged_at`) in the `/referralauths` endpoint.
- The `usualdepartmentid` was initially missing from the `/providers` endpoint but was successfully retrieved by using the `showusualdepartmentguessthreshold` parameter in the `/providers/{providerid}` call.

## Next Steps:
- Depending on future requirements, consider alternative data sources or strategies for the currently unavailable API data (e.g., manual entry or external databases).