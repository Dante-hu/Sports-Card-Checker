# test_wantlist.py

import pytest
import subprocess
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

pytestmark = pytest.mark.no_auto_clean


# -------------------------------
# Fixtures
# -------------------------------
@pytest.fixture(scope="session", autouse=True)
def import_all_cards_once():
    print("\nImporting all cards for Wantlist test...")
    subprocess.run(
        ["python", "-m", "scripts.import_cards_from_output"], cwd="../../..", check=True
    )
    time.sleep(8)
    yield


# -------------------------------
# Helper Functions
# -------------------------------
def find_and_click_card(driver, wait, player_name: str):
    card = wait.until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                f"//p[contains(text(),'{player_name}')]//ancestor::div[contains(@class,'card-tile')]",
            )
        )
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
    card.click()
    return card


def add_to_wantlist(driver, wait, player_name: str):
    find_and_click_card(driver, wait, player_name)
    add_btn = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Add to Wantlist')]")
        )
    )
    add_btn.click()
    wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//div[contains(@class,'cards-toast') and contains(text(),'Added to Wantlist')]",
            )
        )
    )
    driver.execute_script(
        "const ov = document.querySelector('.card-overlay'); if (ov) ov.click();"
    )
    time.sleep(0.5)


def remove_from_wantlist(driver, wait):
    remove_btn = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(text(), 'Remove from Wantlist')]")
        )
    )
    remove_btn.click()
    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//h3[contains(text(),'Remove from Wantlist')]")
        )
    )
    driver.find_element(By.XPATH, "//button[contains(text(),'Confirm')]").click()
    wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//div[contains(@class,'cards-toast') and contains(text(),'Removed from Wantlist')]",
            )
        )
    )
    driver.execute_script(
        "const ov = document.querySelector('.card-overlay'); if (ov) ov.click();"
    )
    time.sleep(0.5)


# -------------------------------
# Main Test
# -------------------------------
def test_wantlist_full_flow(driver, wait, test_user_data, import_all_cards_once):
    email = test_user_data["email"]
    print(f"\nFull Wantlist Flow → {email}")

    # 1. Sign up
    driver.get("http://localhost:5173/signup")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
    driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(email)
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(
        test_user_data["password"]
    )
    driver.find_element(
        By.CSS_SELECTOR, "input[placeholder*='favourite team']"
    ).send_keys("Maple Leafs")
    driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Answer']").send_keys(
        "Toronto"
    )
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait.until(EC.url_contains("/cards"))
    print("Signed up & logged in")

    # 2. Add Victor Wembanyama to Wantlist
    driver.get("http://localhost:5173/cards")
    search = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Search']")
    search.clear()
    search.send_keys("Victor Wembanyama")
    search.send_keys("\n")

    add_to_wantlist(driver, wait, "Victor Wembanyama")
    print("Added Wembanyama to Wantlist")

    # 3. Add Connor McDavid too
    driver.get("http://localhost:5173/cards")
    search = driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Search']")
    search.clear()
    search.send_keys("Connor McDavid")
    search.send_keys("\n")

    add_to_wantlist(driver, wait, "Connor McDavid")
    print("Added McDavid to Wantlist")

    # 4. Go to Wantlist page → verify both cards are there
    driver.get("http://localhost:5173/wantlist")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".card-tile")))

    wemby = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//p[contains(text(),'Victor Wembanyama')]")
        )
    )
    mcdavid = driver.find_element(By.XPATH, "//p[contains(text(),'Connor McDavid')]")

    assert wemby.is_displayed()
    assert mcdavid.is_displayed()
    print("Both cards visible in Wantlist")

    # 5. Remove Wembanyama
    find_and_click_card(driver, wait, "Victor Wembanyama")
    remove_from_wantlist(driver, wait)
    print("Removed Wembanyama from Wantlist")

    # 6. Verify only McDavid remains
    driver.get("http://localhost:5173/wantlist")
    remaining = driver.find_elements(By.XPATH, "//p[contains(text(),'Connor McDavid')]")
    removed = driver.find_elements(
        By.XPATH, "//p[contains(text(),'Victor Wembanyama')]"
    )

    assert len(remaining) > 0
    assert len(removed) == 0
    print("Only McDavid remains")

    # 7. Remove McDavid → empty list
    find_and_click_card(driver, wait, "Connor McDavid")
    remove_from_wantlist(driver, wait)

    driver.get("http://localhost:5173/wantlist")
    empty_msg = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//p[contains(text(),'Your wantlist is empty')]")
        )
    )
    assert empty_msg.is_displayed()
    print("Wantlist is now empty!")

    print("\nWANTLIST FULL FLOW TEST → 100% PASSED")
