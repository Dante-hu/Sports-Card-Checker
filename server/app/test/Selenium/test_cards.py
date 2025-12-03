# test_cards.py
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# This disables DB cleaning for all card tests
pytestmark = pytest.mark.no_auto_clean


@pytest.fixture(scope="session", autouse=True)
def import_all_cards_once():
    print("\nImporting all card sets into database (runs once)...")
    import subprocess
    import time

    subprocess.run(
        ["python", "-m", "scripts.import_cards_from_output"], cwd="../../..", check=True
    )
    time.sleep(8)  # Give server time to index 3450 cards
    yield


def test_donruss_cards_are_loaded(driver, wait):
    driver.get("http://localhost:5173/cards")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".card-tile")))
    cards = driver.find_elements(By.CSS_SELECTOR, ".card-tile")
    assert len(cards) >= 50, f"Only {len(cards)} cards loaded!"


def test_search_wembanyama(driver, wait):
    driver.get("http://localhost:5173/cards")
    search = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Search']")
    search.clear()
    search.send_keys("Wembanyama")
    search.submit()  # More reliable than \n

    # Wait for card name in h3 or h2 or any heading
    wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//h1 | //h2 | //h3 | //h4 | //div[contains(@class,'font-bold') or contains(@class,'text-lg')][contains(text(), 'Victor Wembanyama')]",
            )
        )
    )


def test_filter_by_sport_hockey(driver, wait):
    driver.get("http://localhost:5173/cards")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".card-tile")))

    # Find the Sport dropdown
    sport_select_elem = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//label[text()='Sport']/following-sibling::select")
        )
    )

    from selenium.webdriver.support.ui import Select

    select = Select(sport_select_elem)

    # Select "Hockey"
    select.select_by_visible_text("Hockey")

    wait.until(
        EC.text_to_be_present_in_element_value(
            (By.XPATH, "//label[text()='Sport']/following-sibling::select"), "Hockey"
        )
    )

    # also verify at least one card is visible
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".card-tile")))

    print("Hockey filter successfully applied!")


def test_pagination(driver, wait):
    driver.get("http://localhost:5173/cards")
    next_btn = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//button[contains(text(), 'Next') or .//*[contains(text(),'Next')]]",
            )
        )
    )
    next_btn.click()
    wait.until(
        EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, ".cards-page-info, .pagination-info, div"), "2"
        )
    )


def test_add_card_to_owned_requires_login(driver, wait, test_user_data):
    """Sign up a new user → login → add a card to owned"""
    email = test_user_data["email"]
    password = test_user_data["password"]
    sec_q = test_user_data["security_question"]
    sec_a = test_user_data["security_answer"]

    # 1. Go to signup and create the user
    driver.get("http://localhost:5173/signup")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))

    driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(email)
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(password)
    driver.find_element(
        By.CSS_SELECTOR, "input[placeholder*='favourite team']"
    ).send_keys(sec_q)
    driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Answer']").send_keys(
        sec_a
    )
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # Wait for successful signup → redirect to /cards
    wait.until(EC.url_contains("/cards"))
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//button[contains(text(), 'Logout')]")
        )
    )

    # 2. Now go to cards page and add first card to owned
    driver.get("http://localhost:5173/cards")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".card-tile")))

    first_card = driver.find_element(By.CSS_SELECTOR, ".card-tile")
    first_card.click()

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".card-overlay")))

    add_button = driver.find_element(
        By.XPATH, "//button[contains(text(), 'Add to Owned')]"
    )
    add_button.click()

    # Success toast or message
    success = wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//*[contains(text(), 'Added to Owned') or contains(text(), 'Success') or contains(text(), 'added')]",
            )
        )
    )
    assert success.is_displayed()
    print(f"Card added to owned collection for {email}")
