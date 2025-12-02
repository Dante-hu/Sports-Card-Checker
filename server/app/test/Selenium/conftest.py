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

# Database configuration - same as your main app
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres123@localhost:5432/sports_card_checker",
)


@pytest.fixture(scope="session")
def db_connection():
    """Create a database connection for test setup/teardown"""
    conn = psycopg2.connect(DATABASE_URL)
    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def clean_database(db_connection):
    """Clean the database before each test"""
    # Skip database cleaning for tests that don't need it
    # (useful for read-only tests)
    yield
    # Clean after test runs
    with db_connection.cursor() as cursor:
        # Disable foreign key checks temporarily
        cursor.execute("SET session_replication_role = 'replica';")

        # Get all tables (excluding alembic_version for migrations)
        cursor.execute(
            """
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename NOT IN ('alembic_version')
        """
        )

        tables = cursor.fetchall()

        # Truncate all tables
        for table in tables:
            cursor.execute(
                sql.SQL("TRUNCATE TABLE {} CASCADE").format(sql.Identifier(table[0]))
            )

        # Re-enable foreign key checks
        cursor.execute("SET session_replication_role = 'origin';")
        db_connection.commit()


@pytest.fixture
def driver():
    """Selenium WebDriver fixture - matches your working test"""
    options = Options()

    # Add options for better stability
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    # Uncomment for headless mode (for CI/CD)
    # options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(5)

    yield driver

    driver.quit()


@pytest.fixture
def wait(driver):
    """WebDriverWait fixture for explicit waits"""
    return WebDriverWait(driver, 10)


@pytest.fixture
def unique_email():
    """Generate a unique email for tests"""
    return f"selenium_{int(time.time())}@example.com"


@pytest.fixture
def test_user_data(unique_email):
    """Test user data for signup/login tests"""
    return {
        "email": unique_email,
        "password": "S3lenium!",
        "security_question": "What is your favourite team?",
        "security_answer": "Maple Leafs",
    }
