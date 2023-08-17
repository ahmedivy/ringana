import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By


load_dotenv()

email = os.getenv("RINGANA_EMAIL")
password = os.getenv("RINGANA_PASSWORD")

BASE_URL = "https://lilyairich.ringana.com/login/?lang=en"
TEAMS_URL = "https://lilyairich.ringana.com/mein-team/?lang=en"

# Login, online office, team and customers, click on partner, export


def main():
    driver = webdriver.Chrome()
    driver.get(BASE_URL)

    driver.maximize_window()

    cookies_btn = "Accept all"
    cookies_btn = driver.find_element(By.XPATH, f"//button[contains(text(), '{cookies_btn}')]")
    cookies_btn.click()

    email_input = driver.find_element(By.NAME, "email")
    email_input.send_keys(email)

    login_button = driver.find_element(By.ID, "loginButton")
    login_button.click()

    time.sleep(3)
    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys(password)

    login_button = driver.find_element(By.ID, "loginButton")
    login_button.click()

    time.sleep(8)

    # teams_btn = 'Team & Customers'
    # teams_btn = driver.find_element(By.XPATH, f"//a[contains(text(), '{teams_btn}')]")
    # teams_btn.click()

    driver.execute_script("window.open('', '_blank');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get(TEAMS_URL)

    partner_btn = 'Partner'
    partner_btn = driver.find_element(By.XPATH, f"//div[contains(text(), '{partner_btn}')]")
    partner_btn.click()

    export_btn = 'Export'
    export_btn = driver.find_element(By.XPATH, f"//span[contains(text(), '{export_btn}')]")
    export_btn.click()

    time.sleep(1)

    while True:
        time.sleep(20)


if __name__ == "__main__":
    main()
