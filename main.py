import os
import time
import sqlite3
import pandas as pd
import resend
from typing import List
from dotenv import load_dotenv
from selenium import webdriver
from collections import namedtuple
from selenium.webdriver.common.by import By


ADD_HTML = """
Hi {first_name} {last_name},

We are happy to welcome you to our team!
"""

REMOVE_HTML = """
Hi {first_name} {last_name},

We are sad to see you go!
Thanks for everything you have done for us!
"""

User = namedtuple("User", ["description", "first_name", "last_name", "customer_number", "email", "country", "salutation"])

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")
email = os.getenv("RINGANA_EMAIL")
password = os.getenv("RINGANA_PASSWORD")
sender_name = os.getenv("SENDER_NAME")
sender_email = os.getenv("SENDER_EMAIL")

BASE_URL = "https://lilyairich.ringana.com/login/?lang=en"
FILE_URL = "https://lilyairich.ringana.com/ref/downloads/?mode=teamsearch&partner=true"


def get_csv():
    for file in os.listdir(os.getcwd()):
        if file.endswith(".csv"):
            return file


def get_df():
    df = pd.read_csv(get_csv(), sep=";")
    df = df[["Description", "First name", "Last name", "Customer number", "Email address", "Invoice - Country", "Salutation"]]
    df = df.rename(columns={
        "Invoice number": "invoice_number",
        "Invoice date": "invoice_date",
        "Description": "description",
        "First name": "first_name",
        "Last name": "last_name",
        "Customer number": "customer_number",
        "Email address": "email",
        "Salutation": "salutation",
        "Invoice - Country": "country"
    })
    return df


def populate_db(conn):
    df = get_df(conn)
    df.to_sql("users", conn, if_exists="append", index=False)


def read_db(conn) -> List[User]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return [User(*user) for user in users]


def read_csv() -> List[User]:
    df = get_df()
    users = df.to_dict("records")
    return [User(**user) for user in users]


def get_new_users(db_users, csv_users) -> List[User]:
    return [user for user in csv_users if user.customer_number not in [db_user.customer_number for db_user in db_users]]


def get_removed_users(db_users, csv_users) -> List[User]:
    return [user for user in db_users if user.customer_number not in [csv_user.customer_number for csv_user in csv_users]]


def send_email(user: User, action: str):
    print("Sending email to: ", user.email)
    params = {
        "from": f"{sender_name} <{sender_email}>",
        "to": [user.email],
        "subject": action == "add" and "Welcome to the team!" or "Goodbye!",
        "html": action == "add" and ADD_HTML.format(first_name=user.first_name, last_name=user.last_name) or REMOVE_HTML.format(first_name=user.first_name, last_name=user.last_name)
    }

    email = resend.Emails.send(params)
    print("Email sent: ", email)


def create_db():

    for file in os.listdir(os.getcwd()):
        if file.endswith(".db"):
            conn = sqlite3.connect(file)
            return conn

    conn = sqlite3.connect("ringana.db")

    stmt = """
    CREATE TABLE IF NOT EXISTS users (
        description TEXT,
        first_name TEXT,
        last_name TEXT,
        customer_number TEXT PRIMARY KEY,
        email TEXT,
        country TEXT,
        salutation TEXT
    )
    """

    conn.execute(stmt)
    conn.commit()

    populate_db(conn)

    return conn


def delete_csv():
    for file in os.listdir(os.getcwd()):
        if file.endswith(".csv"):
            print("Deleting file: ", file)
            os.remove(file)


def add_user(conn, user: User):
    stmt = """
    INSERT INTO users (description, first_name, last_name, customer_number, email, country, salutation)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    conn.execute(stmt, user)
    conn.commit()


def remove_user(conn, user: User):
    stmt = """
    DELETE FROM users WHERE customer_number = ?
    """

    conn.execute(stmt, (user.customer_number,))
    conn.commit()


def download_file():
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": os.getcwd(),
        })

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(BASE_URL)

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

        driver.execute_script("window.open('', '_blank');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(FILE_URL)

        time.sleep(8)
    except Exception as e:
        print("Error while downloading file: ", e.__class__.__name__)


def main():

    delete_csv()
    download_file()

    conn = create_db()
    db_users = read_db(conn)
    csv_users = read_csv()

    new_users = get_new_users(db_users, csv_users)
    removed_users = get_removed_users(db_users, csv_users)

    for user in new_users:
        send_email(user, "add")

    for user in removed_users:
        send_email(user, "remove")

    for user in new_users:
        add_user(conn, user)

    for user in removed_users:
        remove_user(conn, user)

    conn.close()

    print("Done")

    # Tell stats
    print("New users: ", len(new_users))
    print("Removed users: ", len(removed_users))


if __name__ == "__main__":
    main()
