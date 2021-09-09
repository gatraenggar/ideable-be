from django.test import TestCase
from  users.validators import RegistrationForm

class RegistrationFormTestCase(TestCase):
    def test_valid_paylaod(self):
        """
        Example of a valid payload
        """
        payload = {
            "email": "johndoe@gmail.com",
            "password": "abcd1234",
            "first_name": "John",
            "last_name": "Doe"
        }
        form = RegistrationForm(payload).is_valid()
        self.assertEqual(form, True)

        payload = {
            "email": "johndoe@gmail.com",
            "password": "pass word 1234 5678",
            "first_name": "D",
            "last_name": " R"
        }
        form = RegistrationForm(payload).is_valid()
        self.assertEqual(form, True)

    def test_field_without_alphabet_characters(self):
        """
        Password, first name, & last name should
        contains at least one alphabet character
        """
        payload = {
            "email": "johndoe@gmail.com",
            "password": "           ",
            "first_name": " ",
            "last_name": "."
        }
        form = RegistrationForm(payload).is_valid()
        self.assertEqual(form, False)

    def test_non_alphabet_field_characters(self):
        """
        last_name & first_name could only contains
        alphabets, colon, and space, while password is alowed
        """
        payload = {
            "email": "johndoe@gmail.com",
            "password": "!@#$%^&*()_{}:\">?\\",
            "first_name": "J?",
            "last_name": "Doe 2"
        }
        form = RegistrationForm(payload).is_valid()
        self.assertEqual(form, False)

    def test_random(self):
        """
        random payload test
        """
        payload = {
            "email": " johndoe@gmail.com",
            "password": "\n\n\n\n\n\n\n\n",
            "first_name": "\njohn",
            "last_name": "\ndoe"
        }
        form = RegistrationForm(payload).is_valid()
        self.assertEqual(form, False)

