# conftest_selenium.py
import os
import pytest
import time
import psycopg2
from psycopg2 import sql
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres123@localhost:5432/sports_card_checker",
)



# register marker 
def pytest_configure(config):
    """Register custom markers to avoid pytest warnings"""
    config.addinivalue_line("markers", "no_auto_clean: skip auto DB cleanup (for card E2E tests)")


@pytest.fixture(scope="session")
def db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def clean_database(db_connection, request):
    """Clean DB after each test — unless marked with @pytest.mark.no_auto_clean"""
    yield

    # Skip cleanup if test/file has the marker
    if request.node.get_closest_marker("no_auto_clean"):
        return

    with db_connection.cursor() as cursor:
        cursor.execute("SET session_replication_role = 'replica';")
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename NOT IN ('alembic_version')
        """)
        for (table,) in cursor.fetchall():
            cursor.execute(sql.SQL("TRUNCATE TABLE {} CASCADE").format(sql.Identifier(table)))
        cursor.execute("SET session_replication_role = 'origin';")
        db_connection.commit()


@pytest.fixture
def driver():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)
    yield driver
    driver.quit()


@pytest.fixture
def wait(driver):
    return WebDriverWait(driver, 10)


@pytest.fixture
def unique_email():
    return f"selenium_{int(time.time())}_{os.getpid()}@example.com"


@pytest.fixture
def test_user_data(unique_email):
    return {
        "email": unique_email,
        "password": "S3lenium!",
        "security_question": "What is your favourite team?",
        "security_answer": "Maple Leafs",
    }