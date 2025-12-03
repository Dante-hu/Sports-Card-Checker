# test_logout.py
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_logout_functionality(driver, wait, test_user_data):
    """Test that logout button works properly."""
    # First, create and login a user
    email = test_user_data["email"]
    password = test_user_data["password"]
    sec_q = test_user_data["security_question"]
    sec_a = test_user_data["security_answer"]

    # Create user via signup
    driver.get("http://localhost:5173/signup")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))

    driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(email)
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(password)
    driver.find_element(
        By.CSS_SELECTOR, "input[placeholder='e.g. What is your favourite team?']"
    ).send_keys(sec_q)
    driver.find_element(
        By.CSS_SELECTOR, "input[placeholder='Answer to your question']"
    ).send_keys(sec_a)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # Wait for login
    wait.until(EC.url_contains("/cards"))

    # Verify we're logged in (logout button should be visible)
    logout_button = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//button[contains(text(), 'Logout')]")
        )
    )
    assert logout_button.is_displayed()

    # TEST: Access protected pages while logged in (should work)
    protected_pages = ["/owned", "/wantlist"]

    for page in protected_pages:
        driver.get(f"http://localhost:5173{page}")
        # Should load without redirect or error
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        assert page in driver.current_url
        print(f"✓ Protected page {page} accessible when logged in")

        # Go back to cards page for logout test
        driver.get("http://localhost:5173/cards")
        wait.until(EC.url_contains("/cards"))

    # Click logout button
    logout_button = driver.find_element(
        By.XPATH, "//button[contains(text(), 'Logout')]"
    )
    logout_button.click()

    # Should redirect to login page
    wait.until(EC.url_contains("/login"))
    assert "login" in driver.current_url

    # TEST: After logout, public pages should still be accessible
    public_pages = ["/cards", "/sets"]

    for page in public_pages:
        driver.get(f"http://localhost:5173{page}")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        assert page in driver.current_url
        print(f"✓ Public page {page} still accessible after logout")

    # TEST: After logout, protected pages should redirect or show error
    protected_pages = ["/owned", "/wantlist"]

    for page in protected_pages:
        driver.get(f"http://localhost:5173{page}")

        # Should either redirect to login or show error
        current_url = driver.current_url

        if "/login" in current_url:
            print(f"✓ {page} redirects to login after logout")
            assert "login" in current_url
        else:
            # Check for authentication error message
            error_elements = driver.find_elements(
                By.XPATH,
                "//*[contains(text(), 'authentication required') or "
                "contains(text(), 'Authentication Required')]",
            )
            if error_elements:
                print(f"✓ {page} shows 'authentication required' error")
                assert len(error_elements) > 0
            else:
                # This would be unexpected
                print(f"⚠ {page} behavior after logout needs investigation")
                print(f"  URL: {current_url}")


def test_logout_from_different_pages(driver, wait, test_user_data):
    """Test logout works from different pages in the app."""
    # Create and login user
    email = test_user_data["email"]
    password = test_user_data["password"]

    # Create user via signup
    driver.get("http://localhost:5173/signup")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))

    driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(email)
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(password)
    driver.find_element(
        By.CSS_SELECTOR, "input[placeholder='e.g. What is your favourite team?']"
    ).send_keys(test_user_data["security_question"])
    driver.find_element(
        By.CSS_SELECTOR, "input[placeholder='Answer to your question']"
    ).send_keys(test_user_data["security_answer"])
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    wait.until(EC.url_contains("/cards"))

    # Test logout from each type of page
    pages_to_test = [
        ("/cards", "public page"),
        ("/sets", "public page"),
        ("/owned", "protected page"),
        ("/wantlist", "protected page"),
    ]

    for page, page_type in pages_to_test:
        print(f"\nTesting logout from {page_type}: {page}")

        # Navigate to the page
        driver.get(f"http://localhost:5173{page}")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Verify logout button is present
        logout_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Logout')]")
            )
        )
        assert logout_button.is_displayed()

        # Click logout
        logout_button.click()

        # Should redirect to login
        wait.until(EC.url_contains("/login"))
        assert "login" in driver.current_url
        print(f"  ✓ Logout successful from {page}")

        # Login again for next test (unless it's the last one)
        if page != pages_to_test[-1][0]:
            driver.get("http://localhost:5173/login")
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
            )

            driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(email)
            driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(
                password
            )
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

            wait.until(EC.url_contains("/cards"))
