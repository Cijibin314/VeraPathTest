from django.test import TestCase, Client
from django.urls import reverse
from .models import Referral, Patient, Provider, Practice, UserProfile
from django.contrib.auth.models import User
import os

class LiveReferralDetailsAjaxTest(TestCase):
    def setUp(self):
        # This test will make a live API call to the Athena sandbox.
        # Ensure that ATHENA_CLIENT_ID and ATHENA_CLIENT_SECRET are in your environment.
        if not (os.environ.get('ATHENA_CLIENT_ID') and os.environ.get('ATHENA_CLIENT_SECRET')):
            self.skipTest("Athena credentials not found in environment. Skipping live API test.")

        # --- IMPORTANT: UPDATE THESE VALUES TO MATCH YOUR SANDBOX DATA ---
        self.TEST_ATHENA_PRACTICE_ID = '195900'
        self.TEST_PATIENT_ID = '60178'
        self.TEST_REFERRAL_AUTH_ID = '204044' # This is the ID to search for
        self.TEST_PATIENT_FIRST_NAME = 'Donna'
        self.TEST_PATIENT_LAST_NAME = 'Sandboxtest'
        # ---

        # Create a user, practice, and user profile
        self.user = User.objects.create_user(username='testuser', password='password')
        self.practice, _ = Practice.objects.get_or_create(athena_practice_id=self.TEST_ATHENA_PRACTICE_ID, defaults={'name': 'Test Sandbox Practice'})
        self.user_profile = UserProfile.objects.create(user=self.user, practice=self.practice)

        # Create a provider and patient that are known to exist in the sandbox
        self.provider = Provider.objects.create(
            full_name='Test Provider',
            practice=self.practice,
        )
        self.patient = Patient.objects.create(original_id=self.TEST_PATIENT_ID, first_name=self.TEST_PATIENT_FIRST_NAME, last_name=self.TEST_PATIENT_LAST_NAME)

        # Create a referral instance with an ID that is known to exist for this patient in the sandbox
        self.referral = Referral.objects.create(
            patient=self.patient,
            provider=self.provider,
            athena_document_id=self.TEST_REFERRAL_AUTH_ID,
            referral_date='2025-11-18'
        )

        # Set up the client and log in
        self.client = Client()
        self.client.login(username='testuser', password='password')

    def test_get_live_referral_details_ajax(self):
        """
        Tests the get_referral_details_ajax view by making a live call
        to the Athena sandbox API.
        """
        # --- Making the request to our view ---
        url = reverse('analytics:get_referral_details_ajax', kwargs={'pk': self.referral.pk})
        
        print(f"\nMaking live request to: {url}")
        print(f"Testing with Referral PK: {self.referral.pk}")
        print(f"  - Patient ID: {self.patient.original_id}")
        print(f"  - Practice ID: {self.practice.athena_practice_id}")
        print(f"  - Athena Auth ID: {self.referral.athena_appointment_id}")

        response = self.client.get(url)

        # --- Assertions ---
        # We expect a 200 OK if the referral is found.
        # If it's not found, the view will correctly return a 404, but the test will fail,
        # which is what we want in order to diagnose the problem.
        self.assertEqual(response.status_code, 200, f"API call failed. Response content: {response.content.decode()}")
        
        # Check the content of the JSON response
        response_json = response.json()
        print("Successfully received JSON response from live API:")
        print(response_json)

        self.assertEqual(str(response_json['referralauthid']), self.referral.athena_appointment_id)
        self.assertEqual(str(response_json['patientid']), self.patient.original_id)



