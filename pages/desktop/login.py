import os
import time
import requests
import json


from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.desktop.base import Base

from scripts import util


class Login(Base):
    REGULAR_USER_EMAIL = os.environ.get('REGULAR_USER_EMAIL')
    REGULAR_USER_PASSWORD = os.environ.get('REGULAR_USER_PASSWORD')
    ADMIN_USER_EMAIL = os.environ.get('ADMIN_USER_EMAIL')
    ADMIN_USER_PASSWORD = os.environ.get('ADMIN_USER_PASSWORD')

    _email_locator = (By.NAME, 'email')
    _continue_locator = (By.ID, 'submit-btn')
    _password_locator = (By.ID, 'password')
    _login_btn_locator = (By.ID, 'submit-btn')
    _repeat_password_locator = (By.ID, 'vpassword')
    _age_locator = (By.ID, 'age')
    _code_input_locator = (By.CSS_SELECTOR, '.tooltip-below')

    def fxa_register(self):
        email = f'{util.get_random_string(10)}@restmail.net'
        password = util.get_random_string(10)
        self.find_element(*self._email_locator).send_keys(email)
        self.find_element(*self._continue_locator).click()
        self.wait.until(EC.element_to_be_clickable(self._login_btn_locator))
        self.find_element(*self._password_locator).send_keys(password)
        self.find_element(*self._repeat_password_locator).send_keys(password)
        self.find_element(*self._age_locator).send_keys(23)
        self.find_element(*self._login_btn_locator).click()
        # sleep to allow FxA to process the request and communicate with the email client
        time.sleep(3)
        code = self.restmail(email)
        self.find_element(*self._code_input_locator).send_keys(code)
        self.find_element(*self._login_btn_locator).click()

    def account(self, user):
        if user == 'regular_user':
            self.fxa_login(self.REGULAR_USER_EMAIL, self.REGULAR_USER_PASSWORD)
        elif user == 'admin':
            self.fxa_login(self.ADMIN_USER_EMAIL, self.ADMIN_USER_PASSWORD)

    def fxa_login(self, email, password):
        self.find_element(*self._email_locator).send_keys(email)
        self.find_element(*self._continue_locator).click()
        self.wait.until(EC.element_to_be_clickable(self._login_btn_locator))
        self.find_element(*self._password_locator).send_keys(password)
        self.find_element(*self._login_btn_locator).click()
        self.wait_for_title_update("Add-ons for Firefox")

    def restmail(self, mail):
        response = requests.get(f'https://restmail.net/mail/{mail}', timeout=5)
        message = json.loads(response.text)
        # creating a timed loop to address a possible communication delay between
        # FxA and restmail; this loop polls the endpoint for 20s to await a response
        # and exits is there was no response received in the given amount of time
        timeout_start = time.time()
        if message:
            for key in range(len(message)):
                return message[key]['headers']['x-verify-short-code']
        elif not message:
            while time.time() < timeout_start + 10:
                requests.get(f'https://restmail.net/mail/{mail}', timeout=5)
                continue
            print('Restmail did not receive an email from FxA')            
        else:
            print('Email received but there was an error while processing the verification code')

