Appointments


GET
/v1/{practiceid}/reference/appointmentconfirmationstatus
Get list of appointment confirmation statuses

GET
/v1/{practiceid}/patientappointmentreasons/newpatient
Get list of appointment reasons for new patients

GET
/v1/{practiceid}/patientappointmentreasons/existingpatient
Get list of appointment reasons for existing patients

GET
/v1/{practiceid}/patientappointmentreasons
Get list of appointment reasons

GET
/v1/{practiceid}/mspinsurancetypes
Get list of appointment-specific MSP qualifiers

GET
/v1/{practiceid}/configuration/appointments/chargeentrynotrequiredreasons
Get list of charge entry not required reasons

PUT
/v1/{practiceid}/appointmenttypes/{appointmenttypeid}
Update a appointment type entry.

GET
/v1/{practiceid}/appointmenttypes/{appointmenttypeid}
Get list of appointment types

POST
/v1/{practiceid}/appointmenttypes
Add appointment type

GET
/v1/{practiceid}/appointmenttypes
Get list of appointment types

PUT
/v1/{practiceid}/appointments/{appointmentid}/thirdpartyexternaldata
Update appointment third party external data

POST
/v1/{practiceid}/appointments/{appointmentid}/thirdpartyexternaldata
Add appointment third party external data

GET
/v1/{practiceid}/appointments/{appointmentid}/thirdpartyexternaldata
Get appointment third party external data

DELETE
/v1/{practiceid}/appointments/{appointmentid}/thirdpartyexternaldata
Remove appointment third party external data

PUT
/v1/{practiceid}/appointments/{appointmentid}/thirdpartycodingstatus
Update appointment third party coding status

POST
/v1/{practiceid}/appointments/{appointmentid}/thirdpartycodingstatus
Add appointment third party coding status

GET
/v1/{practiceid}/appointments/{appointmentid}/thirdpartycodingstatus
Get appointment third party coding status

DELETE
/v1/{practiceid}/appointments/{appointmentid}/thirdpartycodingstatus
Remove appointment third party coding status

POST
/v1/{practiceid}/appointments/{appointmentid}/startcheckin
Initiate appointment check-in process

PUT
/v1/{practiceid}/appointments/{appointmentid}/reschedule
Reschedule appointment

PUT
/v1/{practiceid}/appointments/{appointmentid}/notes/{noteid}
Update appointment note

DELETE
/v1/{practiceid}/appointments/{appointmentid}/notes/{noteid}
Delete appointment note

POST
/v1/{practiceid}/appointments/{appointmentid}/notes
Create appointment note

GET
/v1/{practiceid}/appointments/{appointmentid}/notes
Get all appointment notes

GET
/v1/{practiceid}/appointments/{appointmentid}/nativeathenatelehealthroom
Retrieve athenaone telehealth invite url

PUT
/v1/{practiceid}/appointments/{appointmentid}/mspq
Update appointment-specific MSP qualifier

GET
/v1/{practiceid}/appointments/{appointmentid}/mspq
Get appointment-specific MSP qualifier

DELETE
/v1/{practiceid}/appointments/{appointmentid}/mspq
Delete appointment-specific MSP qualifier

PUT
/v1/{practiceid}/appointments/{appointmentid}/freeze
Freeze appointment slot

PUT
/v1/{practiceid}/appointments/{appointmentid}/customfields
Update appointment-level custom fields

PUT
/v1/{practiceid}/appointments/{appointmentid}/confirmationstatus
Update appointment confirmation status

GET
/v1/{practiceid}/appointments/{appointmentid}/confirmationstatus
Get appointment confirmation status

POST
/v1/{practiceid}/appointments/{appointmentid}/checkout
Complete appointment check-out process

POST
/v1/{practiceid}/appointments/{appointmentid}/checkin
Check in this appointment.

GET
/v1/{practiceid}/appointments/{appointmentid}/checkin
Returns the list of conditions required before check-in.

POST
/v1/{practiceid}/appointments/{appointmentid}/chargeentrynotrequired
Add indicator that charge entry is not required on appointment

POST
/v1/{practiceid}/appointments/{appointmentid}/cancelcheckin
Cancel appointment check-in process

PUT
/v1/{practiceid}/appointments/{appointmentid}/cancel
Cancel appointment

PUT
/v1/{practiceid}/appointments/{appointmentid}/accidentdata
Update appointment accident data

GET
/v1/{practiceid}/appointments/{appointmentid}/accidentdata
Get appointment accident data

PUT
/v1/{practiceid}/appointments/{appointmentid}
Book appointment

GET
/v1/{practiceid}/appointments/{appointmentid}
Get appointment details

DELETE
/v1/{practiceid}/appointments/{appointmentid}
Delete open appointment slot
Deletes an open appointment slot, which will no longer allow appointments to be scheduled in that timeslot.

Parameters
Name	Description
practiceid
integer
(path)
practiceid

practiceid
appointmentid
integer
(path)
appointmentid

appointmentid

Execute
Responses
Code	Description	Links
200	
Success

Media type

application/json
Controls Accept header.
Example Value
Schema
{
  "appointmentid": "string"
}
No links

PUT
/v1/{practiceid}/appointments/waitlist/{waitlistid}
Update a wait list entry.

GET
/v1/{practiceid}/appointments/waitlist/{waitlistid}
Get appointment waitlist

DELETE
/v1/{practiceid}/appointments/waitlist/{waitlistid}
Remove an entry from the wait list.

POST
/v1/{practiceid}/appointments/waitlist
Update appointment waitlist

GET
/v1/{practiceid}/appointments/waitlist
Get appointment waitlist

POST
/v1/{practiceid}/appointments/telehealth/deeplink
Create athenaone telehealth deep link join url

GET
/v1/{practiceid}/appointments/report
Get report of booked appointments

POST
/v1/{practiceid}/appointments/open
Create a new appointment slot

GET
/v1/{practiceid}/appointments/open
Get list of open appointment slots

GET
/v1/{practiceid}/appointments/getappointmentidbyhash/{messagehash}
Gets the appointment id tied to the confirmation hash in the appointment confirmation email

POST
/v1/{practiceid}/appointments/expedited
This call will create an appointment and complete the check-in process. In order to use this endpoint, the practice setting 'Expedited Encounters and Deferred Insurance'must be configured.

GET
/v1/{practiceid}/appointments/customfields
Get the list of appointment custom fields

GET
/v1/{practiceid}/appointments/changed/subscription/events
Get list of appointment slot change events to which you can subscribe

POST
/v1/{practiceid}/appointments/changed/subscription
Subscribe to all/specific change events for appointment slots

GET
/v1/{practiceid}/appointments/changed/subscription
Get list of appointment slot change subscription(s)

DELETE
/v1/{practiceid}/appointments/changed/subscription
Unsubscribe to all/specific change events for appointment slots

GET
/v1/{practiceid}/appointments/changed
Get list of changes in appointment slots based on subscribed events

PUT
/v1/{practiceid}/appointments/booked/{appointmentid}
Update booked appointment

GET
/v1/{practiceid}/appointments/booked/multipledepartment
Get list of booked appointments for multiple departments and providers

GET
/v1/{practiceid}/appointments/booked/multiple
Get list of booked appointments by passing multiple appointmentids

GET
/v1/{practiceid}/appointments/booked
Get list of booked appointments

GET
/v1/{practiceid}/appointments/appointmenttypedropdown/mapping
Get list of schedulable appointment metadata

PUT
/v1/{practiceid}/appointments/appointmentreminders/{appointmentreminderid}
Update appointment reminder.

GET
/v1/{practiceid}/appointments/appointmentreminders/{appointmentreminderid}
Get details of an appointment reminder.

DELETE
/v1/{practiceid}/appointments/appointmentreminders/{appointmentreminderid}
Delete an existing reminder.

POST
/v1/{practiceid}/appointments/appointmentreminders
Create appointment reminder

GET
/v1/{practiceid}/appointments/appointmentreminders
Get list of appointment reminders

GET
/v1/{practiceid}/appointmentcancelreasons
Get list of appointment cancellation reasons

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Appointment/{appointmentid}
Get a single appointment

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Appointment
Find appointments within a practice
Chart


GET
/fhir/r4/AllergyIntolerance/{logicalId}
Read

GET
/fhir/r4/AllergyIntolerance
Search (GET)

POST
/fhir/r4/AllergyIntolerance/_search
Search (POST)

GET
/fhir/r4/CarePlan/{logicalId}
Read

GET
/fhir/r4/CarePlan
Search (GET)

POST
/fhir/r4/CarePlan/_search
Search (POST)

GET
/fhir/r4/Condition/{logicalId}
Read

GET
/fhir/r4/Condition
Search (GET)

POST
/fhir/r4/Condition/_search
Search (POST)

GET
/fhir/r4/DiagnosticReport/{logicalId}
Read

GET
/fhir/r4/DiagnosticReport
Search (GET)

POST
/fhir/r4/DiagnosticReport/_search
Search (POST)

GET
/fhir/r4/Goal/{logicalId}
Read

GET
/fhir/r4/Goal
Search (GET)

POST
/fhir/r4/Goal/_search
Search (POST)

GET
/fhir/r4/Immunization/{logicalId}
Read

GET
/fhir/r4/Immunization
Search (GET)

POST
/fhir/r4/Immunization/_search
Search (POST)

GET
/fhir/r4/Media/{logicalId}
Read

GET
/fhir/r4/Medication/{logicalId}
Read

GET
/fhir/r4/Medication
Search (GET)

POST
/fhir/r4/Medication/_search
Search (POST)

GET
/fhir/r4/MedicationDispense
Search (GET)

POST
/fhir/r4/MedicationDispense/_search
Search (POST)

GET
/fhir/r4/MedicationDispense/{logicalId}
Read

GET
/fhir/r4/MedicationRequest/{logicalId}
Read

GET
/fhir/r4/MedicationRequest
Search (GET)

POST
/fhir/r4/MedicationRequest/_search
Search (POST)

GET
/fhir/r4/Observation/{logicalId}
Read

GET
/fhir/r4/Observation
Search (GET)

POST
/fhir/r4/Observation/_search
Search (POST)

GET
/fhir/r4/Procedure/{logicalId}
Read

GET
/fhir/r4/Procedure
Search (GET)

POST
/fhir/r4/Procedure/_search
Search (POST)

GET
/fhir/r4/QuestionnaireResponse
Search (GET)

POST
/fhir/r4/QuestionnaireResponse
Create

POST
/fhir/r4/QuestionnaireResponse/_search
Search (POST)

GET
/fhir/r4/QuestionnaireResponse/{logicalId}
Read

GET
/fhir/r4/Specimen
Search (GET)

POST
/fhir/r4/Specimen/_search
Search (POST)

GET
/fhir/r4/Specimen/{logicalId}
Read

GET
/v1/{practiceid}/chart/encounters/{encounterid}/summary
Get encounter-specific encounter summary content

GET
/v1/{practiceid}/chart/encounter/{encounterid}/eyecare/visualacuity
Retrieves visual acuity measurements associated with the given encounter id.

GET
/v1/{practiceid}/chart/encounter/{encounterid}/eyecare/visioncorrection
Vision correction measurements entered during an encounter.

GET
/v1/{practiceid}/chart/encounter/{encounterid}/eyecare/intraocularpressure
Intraocular Pressure measurements entered for a specific encounter.

GET
/v1/{practiceid}/chart/encounter/{encounterid}/eyecare/eyedilation
Retrieve the eye dilation readings associated with the given encounter id.

GET
/v1/{practiceid}/reference/medications/stopreasons
Get list of mediation stop reasons

GET
/v1/{practiceid}/reference/medications
Search for available medications

GET
/v1/{practiceid}/reference/allergies/severities
Get list of allergy severities

GET
/v1/{practiceid}/reference/allergies/reactions
Get list of allergy reactions

GET
/v1/{practiceid}/reference/allergies
Search for available allergies

PUT
/v1/{practiceid}/patients/{patientid}/ccda
Update patient's CCDA record

GET
/v1/{practiceid}/patients/{patientid}/ccda
Get patient's CCDA record

PUT
/v1/{practiceid}/chart/{patientid}/vitals/{vitalid}
Update vitals reading

POST
/v1/{practiceid}/chart/{patientid}/vitals
Add vitals to patient's chart

GET
/v1/{practiceid}/chart/{patientid}/vitals
List patient's vitals from all sources

PUT
/v1/{practiceid}/chart/{patientid}/vaccines/{vaccineid}
Update patient's vaccine data

DELETE
/v1/{practiceid}/chart/{patientid}/vaccines/{vaccineid}
Remove vaccine from patient's chart

POST
/v1/{practiceid}/chart/{patientid}/vaccines
Add vaccine to patient's chart

GET
/v1/{practiceid}/chart/{patientid}/vaccines
Get list of patient's vaccines

PUT
/v1/{practiceid}/chart/{patientid}/surgicalhistory
Update patient's surgical history data

POST
/v1/{practiceid}/chart/{patientid}/surgicalhistory
Add surgical history data to patient's chart

GET
/v1/{practiceid}/chart/{patientid}/surgicalhistory
Get patient's surgical history data

PUT
/v1/{practiceid}/chart/{patientid}/socialhistory/templates
Set the list of social history questions for this patient.

GET
/v1/{practiceid}/chart/{patientid}/socialhistory/templates
Get patient's social history templates

PUT
/v1/{practiceid}/chart/{patientid}/socialhistory
Update patient's social history data

GET
/v1/{practiceid}/chart/{patientid}/socialhistory
Get patient's social history data

GET
/v1/{practiceid}/chart/{patientid}/ptepisodes
Get patient's list of PT Episodes.

PUT
/v1/{practiceid}/chart/{patientid}/problems/{problemid}
Update patient's problem details

DELETE
/v1/{practiceid}/chart/{patientid}/problems/{problemid}
Remove a problem from patient's problem list

PUT
/v1/{practiceid}/chart/{patientid}/problems/sectionnote
Update the section-wide note for the patient problem section.

PUT
/v1/{practiceid}/chart/{patientid}/problems
Update patient's problem list

POST
/v1/{practiceid}/chart/{patientid}/problems
Add problem to patient's problem list

GET
/v1/{practiceid}/chart/{patientid}/problems
Get patient's problem list

GET
/v1/{practiceid}/chart/{patientid}/perinatalhistory
Get patient's perinatal history

GET
/v1/{practiceid}/chart/{patientid}/patientchartlist
Get list of different charts for the same patient and sample department for each chart

PUT
/v1/{practiceid}/chart/{patientid}/medications/{medicationentryid}
Update patient's medication list

DELETE
/v1/{practiceid}/chart/{patientid}/medications/{medicationentryid}
Hide medication on patient's medication list (mark as hidden)

PUT
/v1/{practiceid}/chart/{patientid}/medications
Update patient's medication list

POST
/v1/{practiceid}/chart/{patientid}/medications
Add medication to patient's medication list

GET
/v1/{practiceid}/chart/{patientid}/medications
Get patient's medication list

PUT
/v1/{practiceid}/chart/{patientid}/medicalhistory
Update patient's medical history data

GET
/v1/{practiceid}/chart/{patientid}/medicalhistory
Get patient's medical history data

GET
/v1/{practiceid}/chart/{patientid}/labresults
Get patient's lab results

PUT
/v1/{practiceid}/chart/{patientid}/gynhistory
Update patient's GYN history

GET
/v1/{practiceid}/chart/{patientid}/gynhistory
Get patient's GYN history

GET
/v1/{practiceid}/chart/{patientid}/gpal
Get patient's GPAL history

GET
/v1/{practiceid}/chart/{patientid}/flowsheets/{snomedcode}
Get patient's problem-specific flowsheet

PUT
/v1/{practiceid}/chart/{patientid}/familyhistory
Update patient's family history

GET
/v1/{practiceid}/chart/{patientid}/familyhistory
Get patient's family history

GET
/v1/{practiceid}/chart/{patientid}/encounters/{appointmentid}/summary
Get appointment-specific encounter summary content

GET
/v1/{practiceid}/chart/{patientid}/encounters
Get list of patient's encounters

GET
/v1/{practiceid}/chart/{patientid}/documentexport/{documentid}
Retrieve created patient chart export document

POST
/v1/{practiceid}/chart/{patientid}/documentexport
Create patient chart export document

PUT
/v1/{practiceid}/chart/{patientid}/careteam
Update patient's care team members

GET
/v1/{practiceid}/chart/{patientid}/careteam
Get patient's care team members

DELETE
/v1/{practiceid}/chart/{patientid}/careteam
Delete member from patient's care team

GET
/v1/{practiceid}/chart/{patientid}/cancercases
Get open cancer cases for the patient and department.

GET
/v1/{practiceid}/chart/{patientid}/analytes
Get list of patient's lab analytes

PUT
/v1/{practiceid}/chart/{patientid}/allergies
Update patient's allergies

GET
/v1/{practiceid}/chart/{patientid}/allergies
Get patient's allergies

GET
/v1/{practiceid}/chart/{patientid}/administeredquestionnairescreeners
Get list of past screening questionnaires for a patient

GET
/v1/{practiceid}/chart/healthhistory/vaccine/changed/subscription/events
Get list of vaccine change events to which you can subscribe

POST
/v1/{practiceid}/chart/healthhistory/vaccine/changed/subscription
Subscribe to all/specific change events for vaccines

GET
/v1/{practiceid}/chart/healthhistory/vaccine/changed/subscription
Get list of vaccine change subscription(s)

DELETE
/v1/{practiceid}/chart/healthhistory/vaccine/changed/subscription
Unsubscribe to all/specific change events for vaccines

GET
/v1/{practiceid}/chart/healthhistory/vaccine/changed
Get list of changes in vaccines based on subscription

GET
/v1/{practiceid}/chart/healthhistory/problems/changed/subscription/events
Get list of problems change events to which you can subscribe

POST
/v1/{practiceid}/chart/healthhistory/problems/changed/subscription
Subscribe to all/specific change events for problems

GET
/v1/{practiceid}/chart/healthhistory/problems/changed/subscription
Get list of problems change subscription(s)

DELETE
/v1/{practiceid}/chart/healthhistory/problems/changed/subscription
Unsubscribe to all/specific change events for problems

GET
/v1/{practiceid}/chart/healthhistory/problems/changed
Get list of changes in problems based on subscribed events

GET
/v1/{practiceid}/chart/healthhistory/medication/changed/subscription/events
Get list of medication list change events to which you can subscribe

POST
/v1/{practiceid}/chart/healthhistory/medication/changed/subscription
Subscribe to all/specific change events for medication list

GET
/v1/{practiceid}/chart/healthhistory/medication/changed/subscription
Get list of medication list change subscription(s)

DELETE
/v1/{practiceid}/chart/healthhistory/medication/changed/subscription
Unsubscribe to all/specific change events for medication list

GET
/v1/{practiceid}/chart/healthhistory/medication/changed
Get list of changes in medication list based on subscribed events

GET
/v1/{practiceid}/chart/healthhistory/familyhistory/changed/subscription/events
Get list of family history change events to which you can subscribe

POST
/v1/{practiceid}/chart/healthhistory/familyhistory/changed/subscription
Subscribe to all/specific change events for family history

GET
/v1/{practiceid}/chart/healthhistory/familyhistory/changed/subscription
Get list of family history change subscription(s)

DELETE
/v1/{practiceid}/chart/healthhistory/familyhistory/changed/subscription
Unsubscribe to all/specific change events for family history

GET
/v1/{practiceid}/chart/healthhistory/familyhistory/changed
Get list of changes in family history based on subscribed events

GET
/v1/{practiceid}/chart/healthhistory/allergies/changed/subscription/events
Get list of allergy change events to which you are subscribed

POST
/v1/{practiceid}/chart/healthhistory/allergies/changed/subscription
Subscribe to all/specific change events for allergies

GET
/v1/{practiceid}/chart/healthhistory/allergies/changed/subscription
Get list of allergy change subscription(s)

DELETE
/v1/{practiceid}/chart/healthhistory/allergies/changed/subscription
Unsubscribe to all/specific change events for allergies

GET
/v1/{practiceid}/chart/healthhistory/allergies/changed
Get list of changes in allergies based on subscribed events

GET
/v1/{practiceid}/chart/configuration/vitals
Get list of practice-configured vitals fields

GET
/v1/{practiceid}/chart/configuration/socialhistory
Get list of social history questions and templates used by this practice

GET
/v1/{practiceid}/chart/configuration/recipientclasses
Get list of care team recipient classes

GET
/v1/{practiceid}/chart/configuration/medicalhistory
Get list of medical history questions used by this practice

GET
/v1/{practiceid}/chart/configuration/gynhistory
Get list of GYN history questions asked by this practice

GET
/v1/{practiceid}/chart/configuration/flowsheettemplates/{snomedcode}
Get list of problem-specific flowsheet templates

GET
/v1/{practiceid}/ccda/{patientid}/vitals
Get patient's vitals

GET
/v1/{practiceid}/ccda/{patientid}/ccdaexport
Retrieve CCDA document

POST
/v1/{practiceid}/riskgaps/modelagnosticsuspectedconditions
Add suspected diagnosis gaps for non CMS-HCC models to patient chart

DELETE
/v1/{practiceid}/riskgaps/condition/{conditionid}
Delete diagnosis gap from patient's chart

POST
/v1/{practiceid}/riskgaps/condition/delete
Bulk delete diagnosis gaps from patients' charts

POST
/v1/{practiceid}/riskgaps/condition
Add risk adjustment gaps to patient chart

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Substance/{substanceid}
Get an individual substance by ID

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Procedure/{procedureid}
Get a specific procedure by ID

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Procedure
Gets a list of procedures for a given patient.

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Observation/Vital-{vitalid}
Get an individual vital by ID

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Observation/SocialHistory-{socialhistoryid}
Get an social history observation by ID

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Observation/ResultObservation-{resultobservationid}
Gets a single result observation

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Observation
Gets a list of observations about a given patient.

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/MedicationStatement/{medicationstatementid}
Get a specific medication statement by ID

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/MedicationStatement
Gets a list of medications and statements for a given patient.

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/MedicationOrder/{medicationorderid}
Get a specific medication order by ID

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/MedicationOrder
Gets a list of medications and orders for a given patient.

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/MedicationDispense/{medicationdispenseid}
Get a specific medication dispense by ID

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/MedicationDispense
Gets a list of medications and dispenses for a given patient.

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/MedicationAdministration/{medicationadministrationid}
Get a specific medication administration by ID

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/MedicationAdministration
Gets a list of medications and administrations for a given patient.

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Medication/{medicationid}
Get a specific medication by ID

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Immunization/HistoricalVaccine-{immunizationid}
Get a specific immunization by ID

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Immunization/ClinicalVaccine-{immunizationid}
Get a specific immunization by ID

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Immunization
Find immunizations for a given patient.

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Goal/{goalid}
Get a specific goal by ID

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Goal
Gets a list of goals for a given patient.

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/DiagnosticReport/{labresultid}
Get a single diagnostic report by lab result ID.

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/DiagnosticReport
Find diagnostic reports.

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Condition/Problem-{conditionid}
Get a specific condition (problem) by ID

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Condition
Find conditions

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/ClinicalImpression
Find clinical impresssions for a given patient.

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/CarePlan/CareTeam-{careteamid}
Get a specific care plan by ID

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/CarePlan/AssessPlan-{assessplanid}
Get a specific care plan by ID

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/CarePlan
Gets a list of care plans for a given patient.

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/AllergyIntolerance/{allergyintoleranceid}
Get allergy intolerance details

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/AllergyIntolerance
Find allergy intolerances for a given patient.

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/Procedure/{procedureid}
Get a specific procedure by ID

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/Procedure
Gets a list of procedures for a given patient.

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/Observation/Vital-{vitalid}
Get an individual vital by ID

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/Observation/ResultObservation-{resultobservationid}
Get an individual result observation by ID

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/Observation
Gets a list of observations about a given patient.

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/MedicationStatement/{medicationstatementid}
Get a specific medication statement by ID

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/MedicationStatement
Gets a list of medications and statements for a given patient.

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/MedicationOrder/{medicationorderid}
Get a specific medication order by ID

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/MedicationOrder
Gets a list of medications and orders for a given patient.

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/Medication/{medicationid}
Get a specific medication by ID

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/Immunization/HistoricalVaccine-{immunizationid}
Get a specific immunization by ID

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/Immunization/ClinicalVaccine-{immunizationid}
Get a specific immunization by ID

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/Immunization
Find immunizations for a given patient.

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/DiagnosticReport/{labresultid}
Get a single diagnostic report by lab result ID.

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/DiagnosticReport
Find diagnostic reports.

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/Condition/Problem-{conditionid}
Get a specific condition (problem) by ID

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/Condition
Find conditions by brand and chart

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/AllergyIntolerance/{allergyintoleranceid}
Get allergy intolerance details

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/AllergyIntolerance
Find allergy intolerances for a given patient.
Documents and Forms


GET
/fhir/r4/Binary/{logicalId}
Read

GET
/fhir/r4/Device/{logicalId}
Read

GET
/fhir/r4/Device
Search (GET)

POST
/fhir/r4/Device/_search
Search (POST)

GET
/fhir/r4/DocumentReference/{logicalId}
Read

GET
/fhir/r4/DocumentReference
Search (GET)

POST
/fhir/r4/DocumentReference/_search
Search (POST)

GET
/fhir/r4/ServiceRequest/{logicalId}
Read

GET
/fhir/r4/ServiceRequest
Search (GET)

POST
/fhir/r4/ServiceRequest/_search
Search (POST)

GET
/v1/{practiceid}/patients/clientforms
Get list of client forms

GET
/v1/{practiceid}/staff/{staffusername}/inbox
Get list of tasks assigned to given staff

GET
/v1/{practiceid}/reference/documents/patientcase/closereasons
Get list of close-reasons for patient cases

GET
/v1/{practiceid}/providers/{providerid}/inbox/counts
Get count of tasks assigned to given provider

GET
/v1/{practiceid}/providers/{providerid}/inbox
Get list of tasks assigned to given provider

GET
/v1/{practiceid}/prescriptions/changed/subscription/events
Get list of change events for prescriptions

POST
/v1/{practiceid}/prescriptions/changed/subscription
Subscribe to all/specific change events for prescriptions

GET
/v1/{practiceid}/prescriptions/changed/subscription
Get list of subscribed events for changes in prescriptions

DELETE
/v1/{practiceid}/prescriptions/changed/subscription
Unsubscribe to all/specific events for changes in prescriptions

GET
/v1/{practiceid}/prescriptions/changed
Get list of changes in prescriptions

GET
/v1/{practiceid}/patients/{patientid}/photo/thumbnail
Get patient's photo thumbnail

PUT
/v1/{practiceid}/patients/{patientid}/photo
Update patient's photo

POST
/v1/{practiceid}/patients/{patientid}/photo
Upload patient's photo

GET
/v1/{practiceid}/patients/{patientid}/photo
Get patient's photo

DELETE
/v1/{practiceid}/patients/{patientid}/photo
Delete patient's photo

GET
/v1/{practiceid}/patients/{patientid}/patientcases
Get list of patient cases for given patient

POST
/v1/{practiceid}/patients/{patientid}/medicationhistoryconsentverified
Update patient's medication history consent flag as having been verified

PUT
/v1/{practiceid}/patients/{patientid}/driverslicense
Update patient's driver's license document

POST
/v1/{practiceid}/patients/{patientid}/driverslicense
Add patient's driver's license document

GET
/v1/{practiceid}/patients/{patientid}/driverslicense
Get patient's driver's license document

DELETE
/v1/{practiceid}/patients/{patientid}/driverslicense
Delete patient's driver's license document

GET
/v1/{practiceid}/patients/{patientid}/documents/vaccine
Get list of vaccine documents

GET
/v1/{practiceid}/patients/{patientid}/documents/unknown
Get list of unknown documents for given patient

GET
/v1/{practiceid}/patients/{patientid}/documents/surgicalresult
Get list of surgical-results documents

GET
/v1/{practiceid}/patients/{patientid}/documents/surgery/{surgeryid}
Get specific surgery document

GET
/v1/{practiceid}/patients/{patientid}/documents/surgery
Get list of surgery documents

POST
/v1/{practiceid}/patients/{patientid}/documents/signedorder
Adds a signed order document to patient's chart

GET
/v1/{practiceid}/patients/{patientid}/documents/rto/{rtoid}
Get specific 'return to office' document

GET
/v1/{practiceid}/patients/{patientid}/documents/rto
Get list of 'return to office' documents

PUT
/v1/{practiceid}/patients/{patientid}/documents/prescriptions/{prescriptionid}
Update specific prescription document for given patient

GET
/v1/{practiceid}/patients/{patientid}/documents/prescription/{prescriptionid}/pages/{pageid}
Get specific page from given prescription

GET
/v1/{practiceid}/patients/{patientid}/documents/prescription/{prescriptionid}
Get specific prescription document for given patient

GET
/v1/{practiceid}/patients/{patientid}/documents/prescription
Get list of prescriptions for given patient

GET
/v1/{practiceid}/patients/{patientid}/documents/physicianauth/{physicianauthid}/pages/{pageid}
Get page from physician authorization document

PUT
/v1/{practiceid}/patients/{patientid}/documents/physicianauth/{physicianauthid}
Update selected physician authorization

GET
/v1/{practiceid}/patients/{patientid}/documents/physicianauth/{physicianauthid}
Get selected physician authorization

DELETE
/v1/{practiceid}/patients/{patientid}/documents/physicianauth/{physicianauthid}
Delete selected physician authorization

POST
/v1/{practiceid}/patients/{patientid}/documents/physicianauth
Add a physician authorization document.

GET
/v1/{practiceid}/patients/{patientid}/documents/physicianauth
Get list of physician authorizations for given patient

GET
/v1/{practiceid}/patients/{patientid}/documents/phonemessage/{phonemessageid}/pages/{pageid}
Get specific page from given phone message

PUT
/v1/{practiceid}/patients/{patientid}/documents/phonemessage/{phonemessageid}
Update specific phone message

GET
/v1/{practiceid}/patients/{patientid}/documents/phonemessage/{phonemessageid}
Get specific phone message

DELETE
/v1/{practiceid}/patients/{patientid}/documents/phonemessage/{phonemessageid}
Delete specific phone message

POST
/v1/{practiceid}/patients/{patientid}/documents/phonemessage
Create new phone message for given patient

GET
/v1/{practiceid}/patients/{patientid}/documents/phonemessage
Get list of phone messages for given patient

GET
/v1/{practiceid}/patients/{patientid}/documents/patientrecord
Get list of patient records for given patient

GET
/v1/{practiceid}/patients/{patientid}/documents/patientinfo
Get list of patient information documents for a patient

PUT
/v1/{practiceid}/patients/{patientid}/documents/patientcase/{patientcaseid}/reopen
Re-open patient case document

PUT
/v1/{practiceid}/patients/{patientid}/documents/patientcase/{patientcaseid}/close
Close patient case document

PUT
/v1/{practiceid}/patients/{patientid}/documents/patientcase/{patientcaseid}/assign
Reassign patient case document

PUT
/v1/{practiceid}/patients/{patientid}/documents/patientcase/{patientcaseid}
Update patient case document for a patient

GET
/v1/{practiceid}/patients/{patientid}/documents/patientcase/{patientcaseid}
Get patient case document for a patient

GET
/v1/{practiceid}/patients/{patientid}/documents/patientcase/attachment/{patientcasefileid}
Get patient case document's attachmemt

POST
/v1/{practiceid}/patients/{patientid}/documents/patientcase
Add patient case document for a patient

GET
/v1/{practiceid}/patients/{patientid}/documents/patientcase
Get list of patient case documents for a patient

PUT
/v1/{practiceid}/patients/{patientid}/documents/orders/referral/{referraldocumentid}/reopen
Reopens a closed referral order

PUT
/v1/{practiceid}/patients/{patientid}/documents/orders/referral/{referraldocumentid}/close
Closes a referral order

GET
/v1/{practiceid}/patients/{patientid}/documents/order/{orderid}/pages/{pageid}
Get page from patient's order document

GET
/v1/{practiceid}/patients/{patientid}/documents/order/{orderid}
Get patient's order document

DELETE
/v1/{practiceid}/patients/{patientid}/documents/order/{orderid}
Mark patient's order document as deleted

GET
/v1/{practiceid}/patients/{patientid}/documents/order
Get list of patient's orders

GET
/v1/{practiceid}/patients/{patientid}/documents/officenote
Get patient's office note document

GET
/v1/{practiceid}/patients/{patientid}/documents/mednotification
Get patient's medication notification document

GET
/v1/{practiceid}/patients/{patientid}/documents/medicalrecord/{medicalrecordid}/pages/{pageid}
Get page from patient's medical record document

GET
/v1/{practiceid}/patients/{patientid}/documents/medicalrecord/{medicalrecordid}/originaldocument
Get patient's original medical record document

PUT
/v1/{practiceid}/patients/{patientid}/documents/medicalrecord/{medicalrecordid}
Update patient's medical record document

GET
/v1/{practiceid}/patients/{patientid}/documents/medicalrecord/{medicalrecordid}
Get patient's medical record document

DELETE
/v1/{practiceid}/patients/{patientid}/documents/medicalrecord/{medicalrecordid}
Mark patient's medical record document as deleted

POST
/v1/{practiceid}/patients/{patientid}/documents/medicalrecord
Add medical record document to patient's chart

GET
/v1/{practiceid}/patients/{patientid}/documents/medicalrecord
Get list of patient's medical record documents

GET
/v1/{practiceid}/patients/{patientid}/documents/letter/{letterid}
Get patient's letter document

GET
/v1/{practiceid}/patients/{patientid}/documents/letter
Get list of patient's letter documents

GET
/v1/{practiceid}/patients/{patientid}/documents/labresult/{labresultid}/pages/{pageid}
Get page from patient's lab result document

GET
/v1/{practiceid}/patients/{patientid}/documents/labresult/{labresultid}/originaldocument
Get patient's original lab result document

PUT
/v1/{practiceid}/patients/{patientid}/documents/labresult/{labresultid}
Update patient's lab result document

GET
/v1/{practiceid}/patients/{patientid}/documents/labresult/{labresultid}
Get patient's lab result document

DELETE
/v1/{practiceid}/patients/{patientid}/documents/labresult/{labresultid}
Mark patient's lab result document as deleted

POST
/v1/{practiceid}/patients/{patientid}/documents/labresult
Add lab result document to patient's chart

GET
/v1/{practiceid}/patients/{patientid}/documents/labresult
Get list of patient's lab result documents

GET
/v1/{practiceid}/patients/{patientid}/documents/interpretation
Get patient's interpretation document

GET
/v1/{practiceid}/patients/{patientid}/documents/inptadmin/{inptadminid}/pages/{pageid}
Get page from patient's inpatient admin document

GET
/v1/{practiceid}/patients/{patientid}/documents/imagingresult/{imagingresultid}/pages/{pageid}
Get page from patient's imaging result document

GET
/v1/{practiceid}/patients/{patientid}/documents/imagingresult/{imagingresultid}/originaldocument
Get patient's original imaging result document

PUT
/v1/{practiceid}/patients/{patientid}/documents/imagingresult/{imagingresultid}
Update patient's imaging result document

GET
/v1/{practiceid}/patients/{patientid}/documents/imagingresult/{imagingresultid}
Get patient's imaging result document

DELETE
/v1/{practiceid}/patients/{patientid}/documents/imagingresult/{imagingresultid}
Mark patient's imaging result document as deleted

POST
/v1/{practiceid}/patients/{patientid}/documents/imagingresult
Add imaging result document to patient's chart

GET
/v1/{practiceid}/patients/{patientid}/documents/imagingresult
Get list of patient's imaging result documents

GET
/v1/{practiceid}/patients/{patientid}/documents/html
Get patient's HTML document

GET
/v1/{practiceid}/patients/{patientid}/documents/hospital
Get patient's hospital document

GET
/v1/{practiceid}/patients/{patientid}/documents/encounterdocument/{encounterdocumentid}/pages/{pageid}
Get page from patient's encounter document

PUT
/v1/{practiceid}/patients/{patientid}/documents/encounterdocument/{encounterdocumentid}
Update patient's encounter document

GET
/v1/{practiceid}/patients/{patientid}/documents/encounterdocument/{encounterdocumentid}
Get patient's encounter document

DELETE
/v1/{practiceid}/patients/{patientid}/documents/encounterdocument/{encounterdocumentid}
Mark patient's encounter document as deleted

POST
/v1/{practiceid}/patients/{patientid}/documents/encounterdocument
Add encounter document to patient's chart

GET
/v1/{practiceid}/patients/{patientid}/documents/encounterdocument
Get list of patient's encounter documents

GET
/v1/{practiceid}/patients/{patientid}/documents/dme/{dmeid}/pages/{pageid}
Get page from patient's DME document

GET
/v1/{practiceid}/patients/{patientid}/documents/dme/{dmeid}
Get patient's DME document

GET
/v1/{practiceid}/patients/{patientid}/documents/dme
Get list of patient's DME documents

GET
/v1/{practiceid}/patients/{patientid}/documents/coversheet
Get list of coversheet documents for patient

GET
/v1/{practiceid}/patients/{patientid}/documents/correctivelens
Get list of corrective lens documents for patient

GET
/v1/{practiceid}/patients/{patientid}/documents/clinicaldocument/{documentid}/xml
Get XML from document

GET
/v1/{practiceid}/patients/{patientid}/documents/clinicaldocument/{clinicaldocumentid}/pages/{pageid}
Get page from patient's clinical document

GET
/v1/{practiceid}/patients/{patientid}/documents/clinicaldocument/{clinicaldocumentid}/originaldocument
Get patient's original clinical document

PUT
/v1/{practiceid}/patients/{patientid}/documents/clinicaldocument/{clinicaldocumentid}
Update patient's clinical document

GET
/v1/{practiceid}/patients/{patientid}/documents/clinicaldocument/{clinicaldocumentid}
Get patient's clinical document

DELETE
/v1/{practiceid}/patients/{patientid}/documents/clinicaldocument/{clinicaldocumentid}
Mark patient's clinical document as deleted

POST
/v1/{practiceid}/patients/{patientid}/documents/clinicaldocument
Add clinical document to patient's chart

GET
/v1/{practiceid}/patients/{patientid}/documents/clinicaldocument
Get list of patient's clinical documents

GET
/v1/{practiceid}/patients/{patientid}/documents/chartabstraction
Get list of patient's chart abstraction documents

GET
/v1/{practiceid}/patients/{patientid}/documents/appointmentrequest
Get list of patient's appointment request documents

GET
/v1/{practiceid}/patients/{patientid}/documents/advertisement
Get list of advertisement documents for patient

GET
/v1/{practiceid}/patients/{patientid}/documents/admin/{adminid}/pages/{pageid}
Get page from patient's admin document

GET
/v1/{practiceid}/patients/{patientid}/documents/admin/{adminid}/originaldocument
Get patient's original admin document

PUT
/v1/{practiceid}/patients/{patientid}/documents/admin/{adminid}
Update patient's admin document

GET
/v1/{practiceid}/patients/{patientid}/documents/admin/{adminid}
Get patient's admin document

DELETE
/v1/{practiceid}/patients/{patientid}/documents/admin/{adminid}
Mark patient's admin document as deleted

POST
/v1/{practiceid}/patients/{patientid}/documents/admin
Add admin document to patient's chart

GET
/v1/{practiceid}/patients/{patientid}/documents/admin
Get list of patient's admin documents

GET
/v1/{practiceid}/patients/{patientid}/documents/acog/{acogid}/html
Get HTML formatted details from ACOG document

GET
/v1/{practiceid}/patients/{patientid}/documents/acog/{acogid}
Get one patient's ACOG document

GET
/v1/{practiceid}/patients/{patientid}/documents/acog
Get list of patient's ACOG documents

POST
/v1/{practiceid}/patients/{patientid}/documents
Add document to patient's chart

GET
/v1/{practiceid}/patients/{patientid}/documents
Get list of patient's documents

GET
/v1/{practiceid}/orders/signedoff/subscription/events
Get list of signed off order change events to which you can subscribe

POST
/v1/{practiceid}/orders/signedoff/subscription
Subscribe to all/specific change events for signed off orders

GET
/v1/{practiceid}/orders/signedoff/subscription
Get list of signed off order change subscription(s)

DELETE
/v1/{practiceid}/orders/signedoff/subscription
Unsubscribe to all/specific change events for signed off orders

GET
/v1/{practiceid}/orders/signedoff
Get signed off orders

GET
/v1/{practiceid}/orders/outstanding
Get outstanding orders

GET
/v1/{practiceid}/orders/changed/subscription/events
Get list of order change events to which you can subscribe

POST
/v1/{practiceid}/orders/changed/subscription
Subscribe to all/specific change events for orders

GET
/v1/{practiceid}/orders/changed/subscription
Get list of order change subscription(s)

DELETE
/v1/{practiceid}/orders/changed/subscription
Unsubscribe to all/specific change events for orders

GET
/v1/{practiceid}/orders/changed
Get list of changes in orders based on subscription

GET
/v1/{practiceid}/labresults/changed/subscription/events
Get list of lab result change events to which you can subscribe

POST
/v1/{practiceid}/labresults/changed/subscription
Subscribe to all/specific change events for lab results

GET
/v1/{practiceid}/labresults/changed/subscription
Get list of lab result change subscription(s)

DELETE
/v1/{practiceid}/labresults/changed/subscription
Unsubscribe to all/specific change events for lab events

GET
/v1/{practiceid}/labresults/changed
Get list of changes in lab results based on subscription

GET
/v1/{practiceid}/imagingresults/changed/subscription/events
Get list of imaging result change events to which you can subscribe

POST
/v1/{practiceid}/imagingresults/changed/subscription
Subscribe to all/specific change events for imaging results

GET
/v1/{practiceid}/imagingresults/changed/subscription
Get list of imaging result change subscription(s)

DELETE
/v1/{practiceid}/imagingresults/changed/subscription
Unsubscribe to all/specific change events for imaging events

GET
/v1/{practiceid}/imagingresults/changed
Get list of changes in imaging results based on subscription

GET
/v1/{practiceid}/healthhistoryforms/{formid}
Get contents of one generic health history form

GET
/v1/{practiceid}/healthhistoryforms
Get list of live health history forms at practice

GET
/v1/{practiceid}/documenttypes
Get list of document types

POST
/v1/{practiceid}/documents/surgery/{surgeryid}/actions
Add an action note to a surgery document

GET
/v1/{practiceid}/documents/surgery/{surgeryid}/actions
Get the action notes of a surgery document

POST
/v1/{practiceid}/documents/physicianauth/{physicianauthid}/actions
Create new action notes for given physician authorization

GET
/v1/{practiceid}/documents/physicianauth/{physicianauthid}/actions
Get action notes for given physician authorization

GET
/v1/{practiceid}/documents/phonemessage/{phonemessageid}/pages/{pageid}
Get specific page from given phone message

POST
/v1/{practiceid}/documents/phonemessage/{phonemessageid}/actions
Create action note for given phone message

GET
/v1/{practiceid}/documents/phonemessage/{phonemessageid}/actions
Get action note for given phone message

PUT
/v1/{practiceid}/documents/phonemessage/{phonemessageid}
Update specific phone message

GET
/v1/{practiceid}/documents/phonemessage/{phonemessageid}
Get specific phone message

POST
/v1/{practiceid}/documents/phonemessage
Create new phone message for given department

GET
/v1/{practiceid}/documents/phonemessage
Get list of phone messages for given department

POST
/v1/{practiceid}/documents/patientcase/{patientcaseid}/actions
This is used to update an action note on a specific document of a type indicated by the URI.

GET
/v1/{practiceid}/documents/patientcase/{patientcaseid}/actions
Get action note for given patient case

GET
/v1/{practiceid}/documents/patientcase/changed/subscription/events
Get list of change events for patient cases

POST
/v1/{practiceid}/documents/patientcase/changed/subscription
Subscribe to all/specific change events for patient cases

GET
/v1/{practiceid}/documents/patientcase/changed/subscription
Get list of subscribed events for changes in patient cases

DELETE
/v1/{practiceid}/documents/patientcase/changed/subscription
Unsubscribe to all/specific events for changes in patient cases

GET
/v1/{practiceid}/documents/patientcase/changed
Get list of changes in patient cases

POST
/v1/{practiceid}/documents/order/{orderid}/actions
Add order document action note

GET
/v1/{practiceid}/documents/order/{orderid}/actions
Get order document's action note

POST
/v1/{practiceid}/documents/medicalrecord/{medicalrecordid}/actions
Add medical record document action note

GET
/v1/{practiceid}/documents/medicalrecord/{medicalrecordid}/actions
Get medical record document's action note

POST
/v1/{practiceid}/documents/letter/{letterid}/actions
Add letter document action note

GET
/v1/{practiceid}/documents/letter/{letterid}/actions
Get letter document's action note

PUT
/v1/{practiceid}/documents/labresult/{labresultid}/close
Close a lab result

POST
/v1/{practiceid}/documents/labresult/{labresultid}/actions
Add lab result document action note

GET
/v1/{practiceid}/documents/labresult/{labresultid}/actions
Get lab result document's action note

PUT
/v1/{practiceid}/documents/labresult/{documentid}/dataentrycompleted
This endpoint is used to apply a document action on a specific document.

PUT
/v1/{practiceid}/documents/imagingresult/{imagingresultid}/close
Close an imaging result

POST
/v1/{practiceid}/documents/imagingresult/{imagingresultid}/actions
Add imaging result document action note

GET
/v1/{practiceid}/documents/imagingresult/{imagingresultid}/actions
Get imaging result document's action note

POST
/v1/{practiceid}/documents/encounterdocument/{encounterdocumentid}/actions
Add encounter document action note

GET
/v1/{practiceid}/documents/encounterdocument/{encounterdocumentid}/actions
Get encounter document's action note

POST
/v1/{practiceid}/documents/clinicaldocument/{clinicaldocumentid}/actions
Add clinical document action note

GET
/v1/{practiceid}/documents/clinicaldocument/{clinicaldocumentid}/actions
Get clinical document's action note

GET
/v1/{practiceid}/documents/admin/{adminid}/pages/{pageid}
Get page from admin document

POST
/v1/{practiceid}/documents/admin/{adminid}/actions
Add admin document action note

GET
/v1/{practiceid}/documents/admin/{adminid}/actions
Get admin document's action notes

PUT
/v1/{practiceid}/documents/admin/{adminid}
Update admin document without specifying patient ID

GET
/v1/{practiceid}/documents/admin/{adminid}
Get specific admin document without specifying patient ID

POST
/v1/{practiceid}/documents/admin
Add admin document without linking to a patient

GET
/v1/{practiceid}/documents/admin
Get list of admin documents not linked to a patient

GET
/v1/{practiceid}/documentassignment/{documentid}
Get possible assignment usernames for document

GET
/v1/{practiceid}/configuration/inbox/staff
Get list of users whom tasks can be assigned for given department

PUT
/v1/{practiceid}/appointments/{appointmentid}/healthhistoryforms/{formid}
Update specific health history forms for given appointment

GET
/v1/{practiceid}/appointments/{appointmentid}/healthhistoryforms/{formid}
Get specific health history forms for given appointment

GET
/v1/{practiceid}/appointments/{appointmentid}/healthhistoryforms
Get list of health history forms for given appointment

POST
/v1/{practiceid}/faxconfirmations
Update fax receive confirmation details

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/DocumentReference/AmbulatorySummary-{patientid}
Get a specific document reference by ID

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/DocumentReference
Gets a list of document references for a given patient.

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Device/{deviceid}
Get a specific device by ID

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Device
Gets a list of devices for a given patient.

GET
/v1/{practiceid}/patients/{patientid}/documents/letter/{letterid}/pages/{pageid}
Get page from patient's letter document
Encounter


GET
/fhir/r4/Encounter/{logicalId}
Read

GET
/fhir/r4/Encounter
Search (GET)

POST
/fhir/r4/Encounter/_search
Search (POST)

POST
/v1/{practiceid}/hpi/transactionid/{transactionid}
Feedback from Elavon for HPI transaction

GET
/v1/{practiceid}/reference/order/vaccine/declinedreasons
Get list of vaccine decline reasons

GET
/v1/{practiceid}/reference/order/vaccine
Get list of orderable vaccines

GET
/v1/{practiceid}/reference/order/referral
Get list of referral order-types

GET
/v1/{practiceid}/reference/order/procedure
Get list of procedures and surgeries

GET
/v1/{practiceid}/reference/order/prescription/frequencies
Get list of dosage frequencies

GET
/v1/{practiceid}/reference/order/prescription/dosagequantityunits
Get list of units for dosage quantities

GET
/v1/{practiceid}/reference/order/prescription
Get list of orderable medication

GET
/v1/{practiceid}/reference/order/patientinfo
Get list of patient information handouts

GET
/v1/{practiceid}/reference/order/other
Get list of other order types

GET
/v1/{practiceid}/reference/order/lab
Get list of orderable Labs

GET
/v1/{practiceid}/reference/order/imaging
Get list of orderable Imaging Orders

GET
/v1/{practiceid}/reference/order/dme
Get list of orderable DMEs

GET
/v1/{practiceid}/reference/clinicalproviderordertype/lab
Get list of labs for CPOT

GET
/v1/{practiceid}/reference/clinicalproviderordertype/imaging
Get list of imaging studies for CPOT

PUT
/v1/{practiceid}/encounter/{encounterid}/services/{serviceid}
Update service information of given encounter

GET
/v1/{practiceid}/encounter/{encounterid}/services/{serviceid}
Get encounter's service information

DELETE
/v1/{practiceid}/encounter/{encounterid}/services/{serviceid}
Delete specific service for given encounter

PUT
/v1/{practiceid}/encounter/{encounterid}/services/note
Update notes for encounter's services

POST
/v1/{practiceid}/encounter/{encounterid}/services
Create a new service attacted to the billing slip of an encounter.

GET
/v1/{practiceid}/encounter/{encounterid}/services
Get list of all services for given encounter

GET
/v1/{practiceid}/encounter/{encounterid}/procedurecodes
Get list of procedure codes available for given encounter

GET
/v1/{practiceid}/encounter/configuration/modifiers
Get list of non-fee affecting modifiers

GET
/v1/{practiceid}/configuration/ordertype
Get list of orderable concept (ordertype or CPOT)

GET
/v1/{practiceid}/configuration/ordersets
Get list of ordersets for given user

GET
/v1/{practiceid}/configuration/encounterreasons
Get the list of configured encounter reasons

POST
/v1/{practiceid}/chart/{patientid}/ordergroups
Create order groups for given patient

GET
/v1/{practiceid}/chart/questionnairescreeners
Get list of questionnaire screeners

PUT
/v1/{practiceid}/chart/encounter/{encounterid}/vitals/{vitalid}
Update vital information for given encounter

DELETE
/v1/{practiceid}/chart/encounter/{encounterid}/vitals/{vitalid}
Delete vital information for given encounter

POST
/v1/{practiceid}/chart/encounter/{encounterid}/vitals
Add new vital information for given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/vitals
Get list of vitals for given encounter

POST
/v1/{practiceid}/chart/encounter/{encounterid}/startexternaldictation
Mark start of external dictation for given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/stageproceduredocumentation
Get Pre/Intra/Post procedure documentation for given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/reviewofsystems/templates
Get list of 'review of systems' findings and notes for given encounter

PUT
/v1/{practiceid}/chart/encounter/{encounterid}/reviewofsystems
Update review of systems findings and notes for given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/reviewofsystems
Get review of systems findings and notes for given encounter

PUT
/v1/{practiceid}/chart/encounter/{encounterid}/questionnairescreeners/scoreonly
Update score against encounter's questionnaire screener

PUT
/v1/{practiceid}/chart/encounter/{encounterid}/questionnairescreeners
Update questionnaire screener for encounter

POST
/v1/{practiceid}/chart/encounter/{encounterid}/questionnairescreeners
Submit questionnaire screener for encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/questionnairescreeners
Get questionnaire screeners for given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/procedurevitals
Vitals entered during the specified procedure stage.

GET
/v1/{practiceid}/chart/encounter/{encounterid}/proceduretimes
Get Procedure times entered during the specified procedure encounter through the encounter id.

GET
/v1/{practiceid}/chart/encounter/{encounterid}/proceduretimeoutchecklist
Get procedure checklist event times for given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/procedureroles
Get Procedure roles entered during the specified procedure encounter through the encounter id.

GET
/v1/{practiceid}/chart/encounter/{encounterid}/proceduredocumentation
Get procedure documentation for given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/presedationassessment
Get Pre-Sedation Assessment for given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/physicalexam/templates
Get template for patient Physical Exam

PUT
/v1/{practiceid}/chart/encounter/{encounterid}/physicalexam
Update list of Physical Exam/Mental Health Exam findings and notes for given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/physicalexam
Get list of Physical Exam/Mental Health Exam findings and notes for given encounter

PUT
/v1/{practiceid}/chart/encounter/{encounterid}/patientgoals/patientinstructions
Update instructions against patient goals

PUT
/v1/{practiceid}/chart/encounter/{encounterid}/patientgoals/freetextgoal
Update patient's free text goal against patient goals

PUT
/v1/{practiceid}/chart/encounter/{encounterid}/patientgoals/discussionnotes
Update discussion notes against patient goals

GET
/v1/{practiceid}/chart/encounter/{encounterid}/patientgoals
Get list of patient goals

POST
/v1/{practiceid}/chart/encounter/{encounterid}/orders/{orderid}/submit
Submit order for given encounter

POST
/v1/{practiceid}/chart/encounter/{encounterid}/orders/{orderid}/returntosubmit
Revert order state to submit status

POST
/v1/{practiceid}/chart/encounter/{encounterid}/orders/{orderid}/deny
Deny specific order request with reasons

GET
/v1/{practiceid}/chart/encounter/{encounterid}/orders/{orderid}/deny
Get denial reasons for selected order

POST
/v1/{practiceid}/chart/encounter/{encounterid}/orders/{orderid}/actions
Create action note to selected order

GET
/v1/{practiceid}/chart/encounter/{encounterid}/orders/{orderid}
Retrieve some data regarding an order, including the list of documents attached to the order. Useful for finding attached letters, prescription renewal chains, and lab/imaging results.

POST
/v1/{practiceid}/chart/encounter/{encounterid}/orders/vaccine
Create new vaccine order

POST
/v1/{practiceid}/chart/encounter/{encounterid}/orders/referral
Create new referral request

POST
/v1/{practiceid}/chart/encounter/{encounterid}/orders/procedure
Create new procedure or surgery order for given encounter

POST
/v1/{practiceid}/chart/encounter/{encounterid}/orders/prescription
Create new prescription order for given encounter

POST
/v1/{practiceid}/chart/encounter/{encounterid}/orders/patientinfo
Create new patient-info order for given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/orders/outstanding
Get list of outstanding orders for given encounter

POST
/v1/{practiceid}/chart/encounter/{encounterid}/orders/other
Create new (other) order (non-standard order)

POST
/v1/{practiceid}/chart/encounter/{encounterid}/orders/lab
Create new lab order for given encounter

POST
/v1/{practiceid}/chart/encounter/{encounterid}/orders/imaging
Create new Imaging order for given encounter

POST
/v1/{practiceid}/chart/encounter/{encounterid}/orders/dme
Create new DME order for given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/orders
Get list of orders for given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/hpi/templates
Get reference template for HPI findings

PUT
/v1/{practiceid}/chart/encounter/{encounterid}/hpi
Update HPI findings for given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/hpi
Get HPI findings for given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/groupnote
Get the groupnote of the group appointment

POST
/v1/{practiceid}/chart/encounter/{encounterid}/externaldictationmessage
Submit external dictation request

POST
/v1/{practiceid}/chart/encounter/{encounterid}/encounterreasons
Add an encounter reason to the given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/encounterreasons
Get list of reasons for given encounter

DELETE
/v1/{practiceid}/chart/encounter/{encounterid}/encounterreasons
Delete an encounter reason from the given encounter

POST
/v1/{practiceid}/chart/encounter/{encounterid}/encounterreasonnote
Set the freetext encounter reason note for the encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/documentsreview
Get list of documents for review in given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/dictationstatus
Get dictation status for given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/dictatablesections
Get list of dictatable sections for given encounter

PUT
/v1/{practiceid}/chart/encounter/{encounterid}/diagnoses/{diagnosisid}
Update selected diagnosis for given encounter

DELETE
/v1/{practiceid}/chart/encounter/{encounterid}/diagnoses/{diagnosisid}
Delete selected diagnosis for given encounter

POST
/v1/{practiceid}/chart/encounter/{encounterid}/diagnoses
Create new diagnosis for given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/diagnoses
Get list of diagnoses for the given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/defaultsearchfacilities
Get default search facility information for given encounter

PUT
/v1/{practiceid}/chart/encounter/{encounterid}/assessment
Update assessment for given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/assessment
Get assessment for given encounter

GET
/v1/{practiceid}/chart/encounter/{encounterid}/ambulatorysurgicalcontent
Get surgical case content in given clinical-note/procedure encounter and encounter location.

PUT
/v1/{practiceid}/chart/encounter/{encounterid}
Update patient location/status encounter information

GET
/v1/{practiceid}/chart/encounter/{encounterid}
Get encounter information

GET
/v1/{practiceid}/chart/configuration/questionnairescreeners
Get list of questionnaire screeners given an appointment-ID or encounter-ID

GET
/v1/{practiceid}/chart/configuration/patientstatuses
Get list of patient statuses

GET
/v1/{practiceid}/chart/configuration/patientlocations
Get list of patient locations

GET
/v1/{practiceid}/chart/configuration/officeordertypes
Get List of Ordertypes

GET
/v1/{practiceid}/chart/configuration/facilities
Get list of facilities

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Encounter/{encounterid}
Get details of a given encounter

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Encounter
Find encounters for a given patient.
Event Notifications


GET
/fhir/r4/Subscription/{id}
Read a subscription by ID

DELETE
/fhir/r4/Subscription/{id}
Delete a subscription

PUT
/fhir/r4/Subscription/{id}
Update an existing subscription

GET
/fhir/r4/SubscriptionTopic
Discover available subscription topics

GET
/fhir/r4/Subscription
List all subscriptions

POST
/fhir/r4/Subscription
Create a new subscription
Hospital


POST
/v1/{practiceid}/visits/{visitid}/visitcharge
Add visit charge to a hospital visit

GET
/v1/{practiceid}/visits/changed/subscription/events
Get list of hospital visits change events to which you can subscribe

POST
/v1/{practiceid}/visits/changed/subscription
Subscribe to all/specific change events for hospital visits

GET
/v1/{practiceid}/visits/changed/subscription
Get list of subscribed events for changes in hospital visits

DELETE
/v1/{practiceid}/visits/changed/subscription
Unsubscribe to all/specific change events for hospital visits

GET
/v1/{practiceid}/visits/changed
Get list of changes in hospital visits based on subscribed events

GET
/v1/{practiceid}/visits
Get list of hospital visits (with filters)

GET
/v1/{practiceid}/surgerycases/changed/subscription/events
Get list of hospital surgical cases change events to which you can subscribe

POST
/v1/{practiceid}/surgerycases/changed/subscription
Subscribe to all/specific change events for hospital surgical cases

GET
/v1/{practiceid}/surgerycases/changed/subscription
Get list of subscribed events for changes in hospital surgical cases

DELETE
/v1/{practiceid}/surgerycases/changed/subscription
Unsubscribe to all/specific change events for hospital surgical cases

GET
/v1/{practiceid}/surgerycases/changed
Get list of changes in surgical cases based on subscribed events

GET
/v1/{practiceid}/stays/{stayid}/vitals
Get patient vitals from inpatient sources based on stay id.

POST
/v1/{practiceid}/stays/{stayid}/transcription/notes
Create a new transcription note for patient stay

GET
/v1/{practiceid}/stays/{stayid}/transcription/notes
Get transcription notes for a patient stay

GET
/v1/{practiceid}/stays/{stayid}/results
Return the lab and imaging results for a given patient stay in the hospital

GET
/v1/{practiceid}/stays/{stayid}/procedures/planned
Get list of planned procedures for a patient stay.

GET
/v1/{practiceid}/stays/{stayid}/procedures/performed
Get list of procedures performed for a patient stay

GET
/v1/{practiceid}/stays/{stayid}/orders/vaccine
Get list of vaccine orders for a stay

GET
/v1/{practiceid}/stays/{stayid}/orders/lab
Get list of lab orders for a stay

GET
/v1/{practiceid}/stays/{stayid}/orders/ivmedication
Get list of IV medication orders for a stay

GET
/v1/{practiceid}/stays/{stayid}/orders/diet
Get list of diet orders for a stay

GET
/v1/{practiceid}/stays/{stayid}/orders/consult
Get list of consult orders for a stay

GET
/v1/{practiceid}/stays/{stayid}/medications
Get list of all medication details for a hospital stay

GET
/v1/{practiceid}/stays/{stayid}/labresults
Get lab results for a patient's visit in the hospital.

GET
/v1/{practiceid}/stays/{stayid}/dischargemedications
Get list of pre-admission and post-discharge medication details for a stay

GET
/v1/{practiceid}/stays/{stayid}/diagnoses
Get list of diagnosis for a stay

GET
/v1/{practiceid}/stays/{stayid}/careteammembers
Get patient's care team members

GET
/v1/{practiceid}/stays/{stayid}/assessments
Get list of assessments for a specific stay

GET
/v1/{practiceid}/stays/{stayid}
Get specific hospital stay details

GET
/v1/{practiceid}/stays/orders/lab/{orderid}
Get specific lab order details

GET
/v1/{practiceid}/stays/configuration/transcribablenotetypes
List of transcribable note types

GET
/v1/{practiceid}/stays/configuration/orders/vaccine
Get reference list of orderable vaccines

GET
/v1/{practiceid}/stays/configuration/orders/lab
Get reference list of orderable labs

GET
/v1/{practiceid}/stays/configuration/orders/ivmedication
Get reference list of orderable IV medications

GET
/v1/{practiceid}/stays/configuration/orders/diet
Get reference list of orderable diets

GET
/v1/{practiceid}/stays/configuration/orders/consult
Get reference list of consult orders

GET
/v1/{practiceid}/stays/changed/subscription/events
Get list of hospital stays change events to which you can subscribe

POST
/v1/{practiceid}/stays/changed/subscription
Subscribe to all/specific change events for hospital stays

GET
/v1/{practiceid}/stays/changed/subscription
Get list of subscribed events for changes in hospital stays

DELETE
/v1/{practiceid}/stays/changed/subscription
Unsubscribe to all/specific change events for hospital stays

GET
/v1/{practiceid}/stays/changed
Get list of changes in hospital stays based on subscribed events

GET
/v1/{practiceid}/stays/all
Get list of hospital stays

GET
/v1/{practiceid}/stays/active/vitals
Get list of vitals of all active hospital stays

GET
/v1/{practiceid}/stays/active/orders/vaccine
Get list of vaccine orders for all patients currently in hospital

GET
/v1/{practiceid}/stays/active/orders/lab
Get list of lab orders for all patients currently in hospital

GET
/v1/{practiceid}/stays/active/orders/ivmedication
Get list of IV medication orders for all patients currently in hospital

GET
/v1/{practiceid}/stays/active/orders/diet
Get list of diet orders for all patients currently in hospital

GET
/v1/{practiceid}/stays/active/orders/consult
Get list of consult orders for all patients currently in hospital

GET
/v1/{practiceid}/stays/active
Get list of active hospital stays

GET
/v1/{practiceid}/orcase/changed/subscription/events
Get list of hospital OR-cases change events to which you can subscribe

POST
/v1/{practiceid}/orcase/changed/subscription
Subscribe to all/specific change events for hospital OR-cases

GET
/v1/{practiceid}/orcase/changed/subscription
Get list of subscribed events for changes in hospital OR-cases

DELETE
/v1/{practiceid}/orcase/changed/subscription
Unsubscribe to all/specific change events for hospital OR-cases

GET
/v1/{practiceid}/orcase/changed
Get list of changes in OR-cases based on subscribed events

PUT
/v1/{practiceid}/inventory/items
Update items in inventory list

POST
/v1/{practiceid}/inventory/items
Add items to inventory list

GET
/v1/{practiceid}/inventory/items
Get list of inventory items

DELETE
/v1/{practiceid}/inventory/items
Delete items from inventory list

GET
/v1/{practiceid}/inpatient/document/clinical/{clinicaldocumentid}
Get specific clinical document by ID

POST
/v1/{practiceid}/inpatient/document/clinical
Add clinical document to inpatient's chart

GET
/v1/{practiceid}/inpatient/document/clinical
Get a list of specific inpatient's clinical document

GET
/v1/{practiceid}/inpatient/document/admin/{admindocumentid}
Get specific admin document of an inpatient

POST
/v1/{practiceid}/inpatient/document/admin
Add inpatient's admin document

GET
/v1/{practiceid}/inpatient/document/admin
Get a list of specific inpatient's admin documents

GET
/v1/{practiceid}/inpatient/configuration/documentlabels
Get reference list of document labels for inpatient documents

GET
/v1/{practiceid}/chart/{patientid}/vitals/inpatient
Get patient vitals from inpatient sources based on patientid

GET
/v1/{practiceid}/chargecodes/changed/subscription/events
Get list of hospital charge codes change events to which you can subscribe

POST
/v1/{practiceid}/chargecodes/changed/subscription
Subscribe to all/specific change events for hospital charge codes

GET
/v1/{practiceid}/chargecodes/changed/subscription
Get list of subscribed events for changes in hospital charge codes

DELETE
/v1/{practiceid}/chargecodes/changed/subscription
Unsubscribe to all/specific change events for hospital charge codes

GET
/v1/{practiceid}/chargecodes/changed
Get list of changes in hospital charge codes based on subscribed events

POST
/v1/{practiceid}/chargecodes
Create hospital charge code

GET
/v1/{practiceid}/chargecodes
Get list of hospital charge codes

GET
/v1/{practiceid}/beds
Get a list of avaible beds in the hospital
Insurance and Financial


GET
/fhir/r4/Coverage/{logicalId}
Read

GET
/fhir/r4/Coverage
Search (GET)

POST
/fhir/r4/Coverage/_search
Search (POST)

POST
/v1/{practiceid}/patients/{patientid}/voidpayment/{epaymentid}
Void an individual payment from an epayment ID.

PUT
/v1/{practiceid}/patients/{patientid}/referralauths/{referralauthid}
Update single referral-authorization

POST
/v1/{practiceid}/patients/{patientid}/referralauths
Submit referral-authorizations

GET
/v1/{practiceid}/patients/{patientid}/referralauths
Get referral-authorizations

POST
/v1/{practiceid}/patients/{patientid}/recordpayment
Record patient's payment information details

POST
/v1/{practiceid}/patients/{patientid}/receipts/{epaymentid}/signed
Submit authorizations for payment receipts

GET
/v1/{practiceid}/patients/{patientid}/receipts/{epaymentid}/signed
Get list of signed e-payment receipts

POST
/v1/{practiceid}/patients/{patientid}/receipts/{epaymentid}/email
Send email of payment-receipt

GET
/v1/{practiceid}/patients/{patientid}/receipts/{epaymentid}/details
Get payment-receipts for an e-payment

GET
/v1/{practiceid}/patients/{patientid}/receipts/{epaymentid}
Get payment-receipts for an e-payment

GET
/v1/{practiceid}/patients/{patientid}/receipts
Get list of payment-receipts

GET
/v1/{practiceid}/patients/{patientid}/prepaymentplans
Retrieve prepayment plans

POST
/v1/{practiceid}/patients/{patientid}/insurances/{insuranceid}/reactivate
Reactivate patient's specific insurance-package

PUT
/v1/{practiceid}/patients/{patientid}/insurances/{insuranceid}/image
Update existing patient's insurance-card image

POST
/v1/{practiceid}/patients/{patientid}/insurances/{insuranceid}/image
Upload patient's insurance-card image

GET
/v1/{practiceid}/patients/{patientid}/insurances/{insuranceid}/image
Get patient's insurance-card image

DELETE
/v1/{practiceid}/patients/{patientid}/insurances/{insuranceid}/image
Delete patient's insurance-card image

PUT
/v1/{practiceid}/patients/{patientid}/insurances/{insuranceid}/ccmenrollmentstatus
Update CCM enrollment status for an insurance

GET
/v1/{practiceid}/patients/{patientid}/insurances/{insuranceid}/ccmenrollmentstatus
Get CCM enrollment status for an insurance

POST
/v1/{practiceid}/patients/{patientid}/insurances/{insuranceid}/benefitdetails
Create patient's insurance benefit-details

GET
/v1/{practiceid}/patients/{patientid}/insurances/{insuranceid}/benefitdetails
Get patient's insurance benefit-details

PUT
/v1/{practiceid}/patients/{patientid}/insurances/{insuranceid}
Update patient's specific insurance-package

DELETE
/v1/{practiceid}/patients/{patientid}/insurances/{insuranceid}
Delete patient's specific insurance-package

POST
/v1/{practiceid}/patients/{patientid}/insurances/prescription/card
Add or Update(POST/PUT) prescription card image for a specified patient.

GET
/v1/{practiceid}/patients/{patientid}/insurances/prescription/card
Get current prescription card image for a specified patient.

DELETE
/v1/{practiceid}/patients/{patientid}/insurances/prescription/card
Remove current prescription card image for a specified patient.

POST
/v1/{practiceid}/patients/{patientid}/insurances/casepolicies
Create patient's specific case policy

PUT
/v1/{practiceid}/patients/{patientid}/insurances
Update patient's insurance package

POST
/v1/{practiceid}/patients/{patientid}/insurances
Create patient's insurance package

GET
/v1/{practiceid}/patients/{patientid}/insurances
Get patient's insurance packages

DELETE
/v1/{practiceid}/patients/{patientid}/insurances
Delete patient's insurance packages

PUT
/v1/{practiceid}/patients/{patientid}/collectpayment/storedcard/{storedcardid}
Update patient's specific credit-card information

POST
/v1/{practiceid}/patients/{patientid}/collectpayment/storedcard/{storedcardid}
Create new patient's specific credit-card

DELETE
/v1/{practiceid}/patients/{patientid}/collectpayment/storedcard/{storedcardid}
Delete patient's specific credit-card information

POST
/v1/{practiceid}/patients/{patientid}/collectpayment/storedcard
Upload new patient's credit-card details

GET
/v1/{practiceid}/patients/{patientid}/collectpayment/storedcard
Get list of patient's credit-card information

POST
/v1/{practiceid}/patients/{patientid}/collectpayment/singleappointment/{appointmentid}
Enter appointment's payment information

GET
/v1/{practiceid}/patients/{patientid}/collectpayment/singleappointment
Get single-appointment contract payment contracts

POST
/v1/{practiceid}/patients/{patientid}/collectpayment/paymentplan
Create patient's payment plan

GET
/v1/{practiceid}/patients/{patientid}/collectpayment/paymentplan
View patient's payment-plan

POST
/v1/{practiceid}/patients/{patientid}/collectpayment/oneyear/{contractid}/emailagreement
Send email containing 1-year contract agreement

POST
/v1/{practiceid}/patients/{patientid}/collectpayment/oneyear/{appointmentid}
Submit authorizations for 1-year contract (appointment)

GET
/v1/{practiceid}/patients/{patientid}/collectpayment/oneyear/{appointmentid}
View authorizations for 1-year contracts (appointment)

GET
/v1/{practiceid}/patients/{patientid}/collectpayment/oneyear
Get list of 1-year contract (department)

POST
/v1/{practiceid}/patients/{patientid}/collectpayment
Enter patient's payment information

GET
/v1/{practiceid}/patients/{patientid}/claims/patientoutstandingdetailed
Full view of patient's open claims

GET
/v1/{practiceid}/patients/{patientid}/claims/patientoutstanding
Get list of patient's outstanding claims

GET
/v1/{practiceid}/patients/{patientid}/claims/patientclosed
Get list of patient's closed claims

GET
/v1/{practiceid}/patients/paymenthistory
View Payment history information

GET
/v1/{practiceid}/misc/singleappointmentcontractterms
Get single-appointment contract payment terms

GET
/v1/{practiceid}/misc/oneyearcontractterms
Get terms for 1-year contract

PUT
/v1/{practiceid}/insurancepackages/configuration/locallyadministered/{insurancepackageid}/reactivate
Re-enable a local insurance package

PUT
/v1/{practiceid}/insurancepackages/configuration/locallyadministered/{insurancepackageid}/deactivate
Disable a local insurance package

PUT
/v1/{practiceid}/insurancepackages/configuration/locallyadministered/{insurancepackageid}
Update local insurance package

POST
/v1/{practiceid}/insurancepackages/configuration/locallyadministered
Create new local insurance package

GET
/v1/{practiceid}/insurancepackages/casepolicies
Get case-policies for insurance packages

GET
/v1/{practiceid}/insurancepackages
Get list of standard insurance packages

POST
/v1/{practiceid}/feeschedules/configuration/procedure
Create fee-schedule for a procedure

DELETE
/v1/{practiceid}/feeschedules/configuration/procedure
Delete fee-schedule for a procedure

GET
/v1/{practiceid}/feeschedules/checkprocedure
Get fee-schedule for a procedure

GET
/v1/{practiceid}/configuration/validnonccpcreditcardmethods
Get list of non-credit-card payment methods

POST
/v1/{practiceid}/claims/{claimid}/note
Create new claim notes

GET
/v1/{practiceid}/claims/{claimid}/claimtransactions
View all claim transactions

PUT
/v1/{practiceid}/claims/{claimid}/claimnotes/override
Update/Override existing note for a claim

GET
/v1/{practiceid}/claims/{claimid}/claimnotes
View all notes for a claim

PUT
/v1/{practiceid}/claims/{claimid}/attachments
Update existing claim attachment

POST
/v1/{practiceid}/claims/{claimid}/attachments
Upload new attachment

GET
/v1/{practiceid}/claims/{claimid}/attachments
Get list of all claim attachments

DELETE
/v1/{practiceid}/claims/{claimid}/attachments
Delete claim attachment

PUT
/v1/{practiceid}/claims/{claimid}
Update individual claim details

GET
/v1/{practiceid}/claims/{claimid}
Get individual claim details

GET
/v1/{practiceid}/claims/customfields
Get claim's custom-fields

GET
/v1/{practiceid}/claims/changed/subscription/events
Get list of change events for claims

POST
/v1/{practiceid}/claims/changed/subscription
Subscribe to all/specific change events for claims

GET
/v1/{practiceid}/claims/changed/subscription
Get list of subscribed events for changes in claims

DELETE
/v1/{practiceid}/claims/changed/subscription
Unsubscribe to all/specific events for changes in claims

GET
/v1/{practiceid}/claims/changed
Get list of changes in claims

GET
/v1/{practiceid}/claims/attachmenttypeclass
Get list of attachment class-type(s)

POST
/v1/{practiceid}/claims
Create new financial claim

GET
/v1/{practiceid}/claims
Get list of claim details

GET
/v1/{practiceid}/ccmenrollmentstatus/changed/subscription/events
Get list of change events for CCM enrollment status

POST
/v1/{practiceid}/ccmenrollmentstatus/changed/subscription
Subscribe to all/specific change events for CCM enrollment status

GET
/v1/{practiceid}/ccmenrollmentstatus/changed/subscription
Get list of subscribed events for changes in CCM enrollment status

DELETE
/v1/{practiceid}/ccmenrollmentstatus/changed/subscription
Unsubscribe to all/specific events for changes in CCM enrollment status

GET
/v1/{practiceid}/ccmenrollmentstatus/changed
Get list of changes in CCM enrollment status

PUT
/v1/{practiceid}/appointments/{appointmentid}/insurances
Update insurance package details for the appointment

GET
/v1/{practiceid}/appointments/{appointmentid}/insurances
Get insurance package details for the appointment

POST
/v1/{practiceid}/appointments/{appointmentid}/claim
Create claim for an appointment

POST
/v1/{practiceid}/generalledger/inventory/consumption
Record consumption of inventory in the general ledger

POST
/v1/{practiceid}/patientpayvendors/{vendorcode}/statements
Record when patient statements are sent out by a third party vendor

POST
/v1/{practiceid}/patientpayvendors/{vendorcode}/payments/{patientpaymentid}/refund
Record a Patient Refund made by a third party vendor

POST
/v1/{practiceid}/patientpayvendors/{vendorcode}/payments
Record a Patient Payment made via a third party vendor

POST
/v1/{practiceid}/patientpayvendors/{vendorcode}/patientenrollment
Enrolls/unenrolls patients from a third party vendor's patient pay services

POST
/v1/{practiceid}/patientpayvendors/{vendorcode}/claimcollections
Send patient claims that are managed by third party vendor to Collections

POST
/v1/{practiceid}/patientpayvendors/{vendorcode}/changeageingownership
Allows third party vendors to indicate who is resposible for managing the dunning level of a claim

POST
/v1/{practiceid}/patientpayvendors/{vendorcode}/adjustingcharges
Record an adjustment to a patient balance made by a third party vendor
Obstetrics (OB) Episode


PUT
/v1/{practiceid}/chart/{patientid}/obepisodes/{obepisodeid}/problemslist
Update problems list of OB episode

PUT
/v1/{practiceid}/chart/{patientid}/obepisodes/{obepisodeid}/obepisodeinfo
Update OB Episode information

PUT
/v1/{practiceid}/chart/{patientid}/obepisodes/{obepisodeid}/menstrualhistory
Update menstrual history

GET
/v1/{practiceid}/chart/{patientid}/obepisodes/{obepisodeid}/html
Get specific OB episode details in HTML format

PUT
/v1/{practiceid}/chart/{patientid}/obepisodes/{obepisodeid}/geneticscreeningandinfectionhistory
Update genetic screening and infection history

PUT
/v1/{practiceid}/chart/{patientid}/obepisodes/{obepisodeid}/flowsheets/{flowsheetid}
Update flowsheet of OB episode

DELETE
/v1/{practiceid}/chart/{patientid}/obepisodes/{obepisodeid}/flowsheets/{flowsheetid}
Delete flowsheet of OB episode

POST
/v1/{practiceid}/chart/{patientid}/obepisodes/{obepisodeid}/flowsheets
Add prenatal flowsheet to OB episode

GET
/v1/{practiceid}/chart/{patientid}/obepisodes/{obepisodeid}/flowsheet/configuration
Get reference field-list for prenatal flowsheet

PUT
/v1/{practiceid}/chart/{patientid}/obepisodes/{obepisodeid}/eddcalculation
Update expected date of delivery information for OB Episode

PUT
/v1/{practiceid}/chart/{patientid}/obepisodes/{obepisodeid}/discussionitems
Update discussion items of OB Episode

PUT
/v1/{practiceid}/chart/{patientid}/obepisodes/{obepisodeid}/dischargeinformation
Update discharge information of OB Episode

PUT
/v1/{practiceid}/chart/{patientid}/obepisodes/{obepisodeid}/deliveryinformation
Update delivery information for OB episode

PUT
/v1/{practiceid}/chart/{patientid}/obepisodes/{obepisodeid}/18to20weekeddupdate
Update expected date of delivery information using 18-20 week inputs

GET
/v1/{practiceid}/chart/{patientid}/obepisodes/{obepisodeid}
Get specific OB episode details

POST
/v1/{practiceid}/chart/{patientid}/obepisodes
Create new OB episode for the patient

GET
/v1/{practiceid}/chart/{patientid}/obepisodes
Get patient's list of OB episodes

GET
/v1/{practiceid}/chart/reference/obdeliveryoutcomes
Get reference list for OB delivery outcomes

GET
/v1/{practiceid}/chart/configuration/obepisodes/geneticscreeningandinfectionhistory/questions
Get reference questionnaire for genetic screening and infection history

GET
/v1/{practiceid}/chart/configuration/obepisodes/discussionitems
Get reference list of discussion items for OB Episode

GET
/v1/{practiceid}/chart/configuration/obdeliverytypes
Get reference list of OB delivery types

GET
/v1/{practiceid}/chart/configuration/obdeliverysites
Get reference list for OB delivery sites
Patient


GET
/fhir/r4/Group/{logicalId}/$export
Export

GET
/fhir/r4/Patient
Search (GET)

POST
/fhir/r4/Patient/_search
Search (POST)

GET
/fhir/r4/Patient/{logicalId}
Read

POST
/fhir/r4/Patient/{logicalId}/$health-cards-issue
Issue Health Card

GET
/fhir/r4/RelatedPerson
Search (GET)

POST
/fhir/r4/RelatedPerson/_search
Search (POST)

GET
/fhir/r4/RelatedPerson/{logicalId}
Read

GET
/v1/{practiceid}/patientsecuremessage/providers/departmentsmapping
Get department mapping information for patient-messaging

PUT
/v1/{practiceid}/patientsecuremessage/markread
This API endpoint updates the specified patient secure message conversations as having been read by the patient or a patient's family member on the patient portal.

GET
/v1/{practiceid}/patientsecuremessage/getavailablemessagetypes
This API endpoint gets the available message types for a given practice.

POST
/v1/{practiceid}/patients/{patientid}/securemessage/{messagethreadid}/reply
Submit new reply to a specific message-thread

GET
/v1/{practiceid}/patients/{patientid}/securemessage/{messagethreadid}/CanPatientReplyToMessage
Get patient's reply-access rights for specific message thread

GET
/v1/{practiceid}/patients/{patientid}/securemessage/{messagethreadid}
Get all messages from patient's specific message-thread

GET
/v1/{practiceid}/patients/{patientid}/securemessage/sentmessages
Get list of sent-messages

GET
/v1/{practiceid}/patients/{patientid}/securemessage/inboxmessages
Get list of inbox messages

GET
/v1/{practiceid}/patients/{patientid}/securemessage/archivedmessages
Get list of archived messages

POST
/v1/{practiceid}/patients/{patientid}/patientsecuremessage/marklabresultread/{messagethreadid}
mark labresult as Read

GET
/v1/{practiceid}/patient/{patientid}/securemessage/providers
input parameters for get provider list complete

GET
/v1/{practiceid}/brand/{brandid}/patients/{patientid}/securemessage/providers/{providerid}/locations
Retrieve available messaging location for given params.

POST
/v1/{practiceid}/patientsatisfaction/results
Upload patient-satisfaction score data

GET
/v1/{practiceid}/patientsatisfaction
Get patient-satisfaction score - for past appointments

PUT
/v1/{practiceid}/patients/{patientid}/securemessage/{messagethreadid}/unarchive
Archives or unarchives a conversation

PUT
/v1/{practiceid}/patients/{patientid}/securemessage/{messagethreadid}/markread
This API endpoint updates the specified patient secure message conversations as having been read by the patient or a patient's family member on the patient portal.

PUT
/v1/{practiceid}/patients/{patientid}/securemessage/{messagethreadid}/archive
Archives or unarchives a conversation

POST
/v1/{practiceid}/patients/{patientid}/securemessage/topractice
This API endpoint sends a Secure Message to a provider on behalf of a patient.

POST
/v1/{practiceid}/patients/{patientid}/securemessage/topatient
This API endpoint sends a Secure Message to a patient.

POST
/v1/{practiceid}/patients/{patientid}/privacyinformationverified
Update patient's privacy information verification details

GET
/v1/{practiceid}/patients/{patientid}/privacyinformationverified
Get patient's privacy information verification details

GET
/v1/{practiceid}/patients/{patientid}/portalstatus
Get patient's portal status

POST
/v1/{practiceid}/patients/{patientid}/portalinvitation
Send invitations to patient portal

GET
/v1/{practiceid}/patients/{patientid}/portalaccess
Get list of users having access to given patient

GET
/v1/{practiceid}/patients/{patientid}/patientstatementimage
Get selected patient-statement in PDF format

GET
/v1/{practiceid}/patients/{patientid}/patientstatement
Get list of patient-statements (optionally with filters)

PUT
/v1/{practiceid}/patients/{patientid}/interfaceconsents
Update patient's interface consents

GET
/v1/{practiceid}/patients/{patientid}/interfaceconsents
Get patient's interface consents

POST
/v1/{practiceid}/patients/{patientid}/dataaccessinfo
Add data-access information to patient's record

PUT
/v1/{practiceid}/patients/{patientid}/customfields
Update custom-field information from patient's records

GET
/v1/{practiceid}/patients/{patientid}/customfields
Get custom-field information from patient's records

PUT
/v1/{practiceid}/patients/{patientid}/chartalert
Update department specific patient's chart-alert

POST
/v1/{practiceid}/patients/{patientid}/chartalert
Create new department specific patient's chart-alert

GET
/v1/{practiceid}/patients/{patientid}/chartalert
Get last modified information of patient's chart specific to a department

DELETE
/v1/{practiceid}/patients/{patientid}/chartalert
Delete department specific alerts for patient's chart changes

PUT
/v1/{practiceid}/patients/{patientid}/authorizations/{releaseauthorizationid}
Update specific release authorization record

GET
/v1/{practiceid}/patients/{patientid}/authorizations/{releaseauthorizationid}
Get specific release authorization record

DELETE
/v1/{practiceid}/patients/{patientid}/authorizations/{releaseauthorizationid}
Delete specific release authorization record

POST
/v1/{practiceid}/patients/{patientid}/authorizations
Add patient's release authorizations and consent details

GET
/v1/{practiceid}/patients/{patientid}/authorizations
Get patient's release authorizations and consent details

GET
/v1/{practiceid}/patients/{patientid}/appointments/{appointmentid}
Get patient's specific appointment

GET
/v1/{practiceid}/patients/{patientid}/appointments
Get list of patient's appointments

PUT
/v1/{practiceid}/patients/{patientid}
Update specific patient record

GET
/v1/{practiceid}/patients/{patientid}
Get specific patient record

GET
/v1/{practiceid}/patients/search
Get list of patients - (optional) visible to a practitioner

GET
/v1/{practiceid}/patients/enhancedbestmatch
Get list of patients - enhanced best matching search criteria

GET
/v1/{practiceid}/patients/customfields/{customfieldid}/{customfieldvalue}
Get list of patients - matching custom-field criteria

GET
/v1/{practiceid}/patients/changed/subscription/events
Get list of change events for patient's records

POST
/v1/{practiceid}/patients/changed/subscription
Subscribe to all/specific change events for patient's records

GET
/v1/{practiceid}/patients/changed/subscription
Get list of subscribed events for changes in patient's records

DELETE
/v1/{practiceid}/patients/changed/subscription
Unsubscribe to all/specific events for changes in patient's records

GET
/v1/{practiceid}/patients/changed
Get list of changes in patient records

POST
/v1/{practiceid}/patients
Create new patient record

GET
/v1/{practiceid}/patients
Get list of patients for a practice

GET
/v1/{practiceid}/configuration/patients/searchtypes
Returns the list of possible search types to utilize with the /patients/search endpoint.

GET
/v1/{practiceid}/configuration/patients/genderidentity
Get reference list of patient's gender identity information

PUT
/v1/{practiceid}/chart/{patientid}/pharmacies/preferred
Update patient's preferred pharmacy

GET
/v1/{practiceid}/chart/{patientid}/pharmacies/preferred
Get patient's preferred pharmacy

DELETE
/v1/{practiceid}/chart/{patientid}/pharmacies/preferred
Delete patient's preferred pharmacy

PUT
/v1/{practiceid}/chart/{patientid}/pharmacies/default
Update patient's default pharmacy

GET
/v1/{practiceid}/chart/{patientid}/pharmacies/default
Get patient's default pharmacy

PUT
/v1/{practiceid}/chart/{patientid}/labs/default
Update patient's default lab information

GET
/v1/{practiceid}/chart/{patientid}/labs/default
Get patient's default lab information

DELETE
/v1/{practiceid}/chart/{patientid}/labs/default
Delete patient's default lab information

PUT
/v1/{practiceid}/chart/{patientid}/imaging/preferred
Update patient's preferred imaging service

GET
/v1/{practiceid}/chart/{patientid}/imaging/preferred
Get patient's preferred imaging service

DELETE
/v1/{practiceid}/chart/{patientid}/imaging/preferred
Delete patient's preferred imaging service

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Patient/{patientid}
Get a single patient

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Patient
Find Patients

POST
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/Patient/{patientid}/$health-cards-issue
Get a SMART health card for a patient

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/Patient/{patientid}
Get a single patient

GET
/v1/{practiceid}/{brandid}/{chartsharinggroupid}/fhir/dstu2/Patient
Find patients by brand and chart
Practice Configuration


GET
/fhir/r4/Location/{logicalId}
Read

GET
/fhir/r4/Location
Search (GET)

POST
/fhir/r4/Location/_search
Search (POST)

GET
/fhir/r4/Organization/{logicalId}
Read

GET
/fhir/r4/Organization
Search (GET)

POST
/fhir/r4/Organization/_search
Search (POST)

PUT
/v1/{practiceid}/usermessages/{username}/{messageid}
Update specific user-message (internal email)

DELETE
/v1/{practiceid}/usermessages/{username}/{messageid}
Delete specific user-message (internal email)

POST
/v1/{practiceid}/usermessages/{username}
Send a new user-message (internal email)

GET
/v1/{practiceid}/usermessages/{username}
Get list of user-messages (internal emails)

GET
/v1/{practiceid}/textmacros
Get list of text-macros

GET
/v1/{practiceid}/states
Get reference list of all states (enabled in athenaNet)

GET
/v1/{practiceid}/slidingfeeplans
Get list of all sliding fee-plans

GET
/v1/{practiceid}/referralsources
Get list of referral sources

GET
/v1/{practiceid}/races
Get reference list of races

POST
/v1/{practiceid}/providers/{providerprofileid}/enrollmentdocs
Upload new enrollment documentation for given provider profile

GET
/v1/{practiceid}/providers/{providerprofileid}/enrollmentdocs
Get list of enrollment documentation for given provider profile

GET
/v1/{practiceid}/practiceinfo
Get list of practice(s), athena-products enabled for the user

GET
/v1/{practiceid}/ping
Return an acknowledgement that request was received and that this API key has access to the given practice.

GET
/v1/{practiceid}/occupations
Get reference list of occupations and their codes

GET
/v1/{practiceid}/mobilecarriers
Get reference list of mobile-carriers

GET
/v1/{practiceid}/misc/topinsurancepackages
Get list of top insurance packages

GET
/v1/{practiceid}/misc/smstermsandconditions
Get SMS opt-in consent forms

GET
/v1/{practiceid}/misc/remindercallsettings
Get reminder-call settings

POST
/v1/{practiceid}/misc/properjsonencoding
Set strict JSON encoding format for API-return data-types

GET
/v1/{practiceid}/misc/properjsonencoding
Get the current status for strict-JSON encoding format setting

DELETE
/v1/{practiceid}/misc/properjsonencoding
Disables setting strict JSON encoding format for API-return data-types

GET
/v1/{practiceid}/misc/portalsettings
Get patient portal setting details

GET
/v1/{practiceid}/misc/patientlocations
Get reference list of patient locations

GET
/v1/{practiceid}/misc/commoninsurancepackages
Get reference list of common insurance packages

GET
/v1/{practiceid}/languages
Get reference list of languages

GET
/v1/{practiceid}/industries
Get reference list of industries and their codes

GET
/v1/{practiceid}/genderidentities
Get reference list of gender identities

GET
/v1/{practiceid}/ethnicities
Get reference list of ethnicities

POST
/v1/{practiceid}/entitynumber
add a new entity number via a MDP call

PUT
/v1/{practiceid}/employers/{employerid}/undelete
Undelete specific employee record

PUT
/v1/{practiceid}/employers/{employerid}
Update specific employee record

GET
/v1/{practiceid}/employers/{employerid}
Get specific employee record

DELETE
/v1/{practiceid}/employers/{employerid}
Delete an employee record

POST
/v1/{practiceid}/employers
Create new employee record

GET
/v1/{practiceid}/employers
Get practice's list of employees

GET
/v1/{practiceid}/departments/{departmentid}/ecommunicationdisclosure
Get legal e-communication disclosure information

GET
/v1/{practiceid}/departments/{departmentid}/checkinrequired
Get list of required fields for patient check-in

GET
/v1/{practiceid}/departments/{departmentid}
Get specific department information

GET
/v1/{practiceid}/departments
Get list of all departments

GET
/v1/{practiceid}/customfields
Get practice's list of custom-fields

GET
/v1/{practiceid}/configuration/chartsharinggroups
Get practice's list of chart-sharing groups

GET
/v1/{practiceid}/communicatorbrands/{communicatorbrandid}
Get specific communicator brand information

GET
/v1/{practiceid}/communicatorbrands
Get practice's list of communicator brands

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Organization/Practice-{practiceid1}
Get information about this practice
Provider


GET
/fhir/r4/CareTeam/{logicalId}
Read

GET
/fhir/r4/CareTeam
Search (GET)

POST
/fhir/r4/CareTeam/_search
Search (POST)

GET
/fhir/r4/Practitioner/{logicalId}
Read

GET
/fhir/r4/Practitioner
Search (GET)

POST
/fhir/r4/Practitioner/_search
Search (POST)

GET
/fhir/r4/Provenance/{logicalId}
Read

GET
/fhir/r4/Provenance
Search (GET)

POST
/fhir/r4/Provenance/_search
Search (POST)

PUT
/v1/{practiceid}/referringproviders/{referringproviderid}
Update information of given referring provider

GET
/v1/{practiceid}/referringproviders/{referringproviderid}
Get information of given referring provider

GET
/v1/{practiceid}/referringproviders/changed/subscription/events
Get list of change events for referring-providers

POST
/v1/{practiceid}/referringproviders/changed/subscription
Subscribe to all/specific change events for referring-providers

GET
/v1/{practiceid}/referringproviders/changed/subscription
Get list of subscribed events for changes in referring-providers

DELETE
/v1/{practiceid}/referringproviders/changed/subscription
Unsubscribe to all/specific events for changes in referring-providers

GET
/v1/{practiceid}/referringproviders/changed
Get list of changes in referring-providers

POST
/v1/{practiceid}/referringproviders
Add new referring provider

GET
/v1/{practiceid}/referringproviders
Get list of referring providers

GET
/v1/{practiceid}/referringprovidernumbers/changed/subscription/events
Get list of change events for referring-provider numbers

POST
/v1/{practiceid}/referringprovidernumbers/changed/subscription
Subscribe to all/specific change events for referring-provider numbers

GET
/v1/{practiceid}/referringprovidernumbers/changed/subscription
Get list of subscribed events for changes in referring-provider numbers

DELETE
/v1/{practiceid}/referringprovidernumbers/changed/subscription
Unsubscribe to all/specific events for changes in referring-provider numbers

GET
/v1/{practiceid}/referringprovidernumbers/changed
Get list of changes in referring-provider numbers

GET
/v1/{practiceid}/reference/providertypes
Get list of provider-types

GET
/v1/{practiceid}/reference/providerspecialties
Get reference list of provider-specialties

PUT
/v1/{practiceid}/providers/{providerid}
Update information of given provider

GET
/v1/{practiceid}/providers/{providerid}
Get information of given provider

DELETE
/v1/{practiceid}/providers/{providerid}
Delete information of given provider

GET
/v1/{practiceid}/providers/dictationsettings
Get list of dictation settings configured for providers

GET
/v1/{practiceid}/providers/changed/subscription/events
Get list of change events for providers

POST
/v1/{practiceid}/providers/changed/subscription
Subscribe to all/specific change events for providers

GET
/v1/{practiceid}/providers/changed/subscription
Get list of subscribed events for changes in providers

DELETE
/v1/{practiceid}/providers/changed/subscription
Unsubscribe to all/specific events for changes in providers

GET
/v1/{practiceid}/providers/changed
Get list of changes in providers

POST
/v1/{practiceid}/providers/addbillingrows
Create new provider billing record(row)

POST
/v1/{practiceid}/providers
Add new provider

GET
/v1/{practiceid}/providers
Get list of all providers

GET
/v1/{practiceid}/providernumbers/changed/subscription/events
Get list of change events for provider numbers

POST
/v1/{practiceid}/providernumbers/changed/subscription
Subscribe to all/specific change events for provider numbers

GET
/v1/{practiceid}/providernumbers/changed/subscription
Get list of subscribed events for changes in provider numbers

DELETE
/v1/{practiceid}/providernumbers/changed/subscription
Unsubscribe to all/specific events for changes in provider numbers

GET
/v1/{practiceid}/providernumbers/changed
Get list of changes in provider numbers

GET
/v1/{practiceid}/personalpronouns
Get the mapping of personal pronouns id to display name.

GET
/v1/{practiceid}/clinicalproviders/{clinicalproviderid}
Get information on given clinical provider

GET
/v1/{practiceid}/clinicalproviders/search
Get list of clinical providers - matching given criteria

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Practitioner/Provider-{providerid}
Get an individual provider

GET
/v1/{practiceid}/{departmentid}/fhir/dstu2/Organization/ClinicalProvider-{clinicalproviderid}
Get an individual clinical provider
Quality Management and Pop Health


PUT
/v1/{practiceid}/chart/{patientid}/riskcontract
Update patient risk contract information

GET
/v1/{practiceid}/chart/{patientid}/riskcontract
Get patient risk contract information

DELETE
/v1/{practiceid}/chart/{patientid}/riskcontract
Delete patient risk contract information

POST
/v1/{practiceid}/chart/{patientid}/qualitymanagement/refresh
Refresh quality measures for given patient

GET
/v1/{practiceid}/chart/{patientid}/qualitymanagement/refresh
Get last created/refresh time of patient's quality measure

GET
/v1/{practiceid}/chart/{patientid}/qualitymanagement/providers
Get list of patient's primary provider and all associated providers

GET
/v1/{practiceid}/chart/{patientid}/qualitymanagement
Get quality measures for given patient

PUT
/v1/{practiceid}/chart/riskcontracts
Bulk Update one/all patient risk contract(s) information

GET
/v1/{practiceid}/chart/riskcontracts
Get One/All patient risk contract(s) information

DELETE
/v1/{practiceid}/chart/riskcontracts
Delete One/All patient risk contract(s) information

PUT
/v1/{practiceid}/populationmanagement/riskcontract
Update basic/default risk contract information

GET
/v1/{practiceid}/populationmanagement/riskcontract
Get basic/default risk contract information