# test_signup.py - using simple fixtures
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def test_signup_and_login_flow(driver, wait, unique_email):
    email = unique_email
    password = "S3lenium!"
    sec_q = "What is your favourite team?"
    sec_a = "Maple Leafs"

    # ============================================================
    # 1. SIGN UP
    # ============================================================
    driver.get("http://localhost:5173/signup")

    # Wait for page to load
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))

    # Fill signup form
    driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(email)
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(password)
    driver.find_element(
        By.CSS_SELECTOR, "input[placeholder='e.g. What is your favourite team?']"
    ).send_keys(sec_q)
    driver.find_element(
        By.CSS_SELECTOR, "input[placeholder='Answer to your question']"
    ).send_keys(sec_a)

    # Submit form
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # Wait for redirect to cards page
    wait.until(EC.url_contains("/cards"))
    assert "/cards" in driver.current_url

    # Additional verification: Check that AppLayout is loaded
    # Look for the logout button which is part of AppLayout
    logout_button = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//button[contains(text(), 'Logout')]")
        )
    )
    assert logout_button.is_displayed()


def test_signup_duplicate_email(driver, wait, test_user_data):
    """Test that signing up with the same email twice fails"""
    # First signup
    driver.get("http://localhost:5173/signup")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))

    driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(
        test_user_data["email"]
    )
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(
        test_user_data["password"]
    )
    driver.find_element(
        By.CSS_SELECTOR, "input[placeholder='e.g. What is your favourite team?']"
    ).send_keys(test_user_data["security_question"])
    driver.find_element(
        By.CSS_SELECTOR, "input[placeholder='Answer to your question']"
    ).send_keys(test_user_data["security_answer"])
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # Wait for redirect
    wait.until(EC.url_contains("/cards"))

    # Logout
    driver.find_element(By.XPATH, "//button[contains(text(), 'Logout')]").click()
    wait.until(EC.url_contains("/login"))

    # Try to sign up with same email again
    driver.get("http://localhost:5173/signup")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))

    driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(
        test_user_data["email"]
    )
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(
        "AnotherPassword123!"
    )
    driver.find_element(
        By.CSS_SELECTOR, "input[placeholder='e.g. What is your favourite team?']"
    ).send_keys("Different question")
    driver.find_element(
        By.CSS_SELECTOR, "input[placeholder='Answer to your question']"
    ).send_keys("Different answer")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # Should show error message (you'll need to adjust based on your error handling)
    # This is just an example - you'll need to check your actual error display
    try:
        error_message = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "error-message"))
        )
        assert (
            "email" in error_message.text.lower()
            or "already" in error_message.text.lower()
        )
    except TimeoutException:
        # If no error message element, maybe the form just doesn't submit
        # Check we're still on signup page
        assert "signup" in driver.current_url
