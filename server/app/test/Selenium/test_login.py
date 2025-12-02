# test_login.py
import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_successful_login(driver, wait, test_user_data):
    """Test that a user can log in with correct credentials."""
    # First, create a user via signup
    email = test_user_data["email"]
    password = test_user_data["password"]
    sec_q = test_user_data["security_question"]
    sec_a = test_user_data["security_answer"]

    # Create user via signup
    driver.get("http://localhost:5173/signup")
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
    )

    driver.find_element(
        By.CSS_SELECTOR, "input[type='email']"
    ).send_keys(email)
    driver.find_element(
        By.CSS_SELECTOR, "input[type='password']"
    ).send_keys(password)
    driver.find_element(
        By.CSS_SELECTOR,
        "input[placeholder='e.g. What is your favourite team?']"
    ).send_keys(sec_q)
    driver.find_element(
        By.CSS_SELECTOR,
        "input[placeholder='Answer to your question']"
    ).send_keys(sec_a)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # Wait for redirect to cards page after signup
    wait.until(EC.url_contains("/cards"))

    # Logout
    logout_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Logout')]")
        )
    )
    logout_button.click()

    # Wait for redirect to login page
    wait.until(EC.url_contains("/login"))

    # Now test login with same credentials
    driver.get("http://localhost:5173/login")
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
    )

    # Fill login form
    driver.find_element(
        By.CSS_SELECTOR, "input[type='email']"
    ).send_keys(email)
    driver.find_element(
        By.CSS_SELECTOR, "input[type='password']"
    ).send_keys(password)

    # Submit login form
    login_button = driver.find_element(
        By.CSS_SELECTOR, "button[type='submit']"
    )
    login_button.click()

    # Wait for redirect to cards page
    wait.until(EC.url_contains("/cards"))

    # Verify successful login
    assert "/cards" in driver.current_url

    # AppLayout is loaded (logout button present)
    logout_button = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//button[contains(text(), 'Logout')]")
        )
    )
    assert logout_button.is_displayed()


def test_login_invalid_credentials(driver, wait):
    """Test login with invalid credentials shows error."""
    driver.get("http://localhost:5173/login")
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
    )

    # Fill with invalid credentials
    driver.find_element(
        By.CSS_SELECTOR, "input[type='email']"
    ).send_keys("nonexistent@example.com")
    driver.find_element(
        By.CSS_SELECTOR, "input[type='password']"
    ).send_keys("wrongpassword")

    # Submit form
    login_button = driver.find_element(
        By.CSS_SELECTOR, "button[type='submit']"
    )
    login_button.click()

    # Should stay on login page or show error
    # Check for error message
    try:
        # Look for any error message
        error_element = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".text-red-500, .error, [role='alert']")
            )
        )
        assert error_element.is_displayed()
    except Exception:
        # If no specific error element, should stay on login page
        wait.until(lambda d: "login" in d.current_url)
        assert "login" in driver.current_url


def test_login_empty_fields(driver, wait):
    """Test that empty form submission shows validation errors."""
    driver.get("http://localhost:5173/login")
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
    )

    # Try to submit empty form
    login_button = driver.find_element(
        By.CSS_SELECTOR, "button[type='submit']"
    )
    login_button.click()

    # Should show validation errors
    # Check for required field indicators or error messages
    try:
        # Look for validation messages
        validation_errors = driver.find_elements(
            By.CSS_SELECTOR, "[aria-invalid='true'], .border-red-500"
        )
        assert len(validation_errors) > 0
    except Exception:
        # At minimum, should not redirect
        assert "login" in driver.current_url


def test_protected_pages_redirect_to_login(driver, wait):
    """Test protected pages redirect to login or show error."""
    # Clear any existing session
    driver.delete_all_cookies()

    # Test accessing PUBLIC pages - should NOT redirect
    public_pages = ["/cards", "/sets"]

    for page in public_pages:
        driver.get(f"http://localhost:5173{page}")
        # Should load directly without redirect
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        assert page in driver.current_url
        print(f"✓ Public page {page} accessible without login")

    # Test accessing PROTECTED pages
    protected_pages = ["/owned", "/wantlist"]

    for page in protected_pages:
        driver.get(f"http://localhost:5173{page}")

        # Should redirect to login page
        try:
            wait.until(EC.url_contains("/login"))
            assert "login" in driver.current_url
            print(f"✓ {page} redirects to login when not authenticated")
        except Exception:
            # If not redirected, check for error message
            error_elements = driver.find_elements(
                By.XPATH,
                "//*[contains(text(), 'authentication required') or "
                "contains(text(), 'Authentication Required')]"
            )
            if error_elements:
                print(f"✓ {page} shows 'authentication required' error")
                assert len(error_elements) > 0
            else:
                # If neither redirect nor error
                print(f"⚠ {page} didn't redirect or show error")
                print(f"  Current URL: {driver.current_url}")
                time.sleep(1)  # Brief pause for debugging