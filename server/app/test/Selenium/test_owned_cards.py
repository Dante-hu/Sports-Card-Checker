# test_owned_cards.py

import pytest
import subprocess
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

pytestmark = pytest.mark.no_auto_clean

# -------------------------------
# Helpers
# -------------------------------

def normalize_text(text: str) -> str:
    return " ".join(text.split())

def find_and_click_card(driver, wait, card_name: str):
    card = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, f"//p[contains(text(),'{card_name}')]//ancestor::div[contains(@class,'card-tile')]")
        )
    )
    card.click()
    return card

def add_to_owned(driver, wait, card_name: str, times=1):
    """Safely add a card multiple times, re-finding elements each time."""
    for _ in range(times):
        find_and_click_card(driver, wait, card_name)
        add_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Add to Owned')]"))
        )
        add_btn.click()
        wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'cards-toast') and contains(text(),'Added')]"))
        )
        driver.execute_script("const ov = document.querySelector('.card-overlay'); if (ov) ov.click();")
        time.sleep(0.3)

def find_card_with_qty(driver, wait, qty_text: str):
    all_cards = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".card-meta-line"))
    )
    for c in all_cards:
        if qty_text in normalize_text(c.text):
            return c
    return None

def remove_from_owned(driver, wait, qty_to_remove: int):
    """Remove a number of copies safely."""
    remove_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Remove from Owned')]"))
    )
    remove_btn.click()
    wait.until(EC.presence_of_element_located((By.XPATH, "//h3[contains(text(),'How many copies')]")))
    qty_input = driver.find_element(By.CSS_SELECTOR, "input[type='number']")
    qty_input.clear()
    qty_input.send_keys(str(qty_to_remove))
    driver.find_element(By.XPATH, "//button[contains(text(),'Confirm')]").click()
    driver.execute_script("const ov = document.querySelector('.card-overlay'); if (ov) ov.click();")
    time.sleep(0.3)

# -------------------------------
# Fixtures
# -------------------------------

@pytest.fixture(scope="session", autouse=True)
def import_all_cards_once():
    print("\nImporting cards once...")
    subprocess.run(["python", "-m", "scripts.import_cards_from_output"], cwd="../../..", check=True)
    time.sleep(8)
    yield

# -------------------------------
# Test
# -------------------------------

def test_owned_cards_full_flow(driver, wait, test_user_data, import_all_cards_once):
    email = test_user_data["email"]
    print(f"\nFull Owned Cards Flow → {email}")

    # --- Sign up ---
    driver.get("http://localhost:5173/signup")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']")))
    driver.find_element(By.CSS_SELECTOR, "input[type='email']").send_keys(email)
    driver.find_element(By.CSS_SELECTOR, "input[type='password']").send_keys(test_user_data["password"])
    driver.find_element(By.CSS_SELECTOR, "input[placeholder*='favourite team']").send_keys("Maple Leafs")
    driver.find_element(By.CSS_SELECTOR, "input[placeholder*='Answer']").send_keys("Toronto")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    wait.until(EC.url_contains("/cards"))
    print("Signed up & logged in")

    # --- Add 1 Connor Bedard ---
    driver.get("http://localhost:5173/cards")
    search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Search']")))
    search_input.clear()
    search_input.send_keys("Connor Bedard\n")
    add_to_owned(driver, wait, "Connor Bedard", times=1)
    print("Added 1 copy")

    # --- Verify x1 ---
    driver.get("http://localhost:5173/owned")
    card = find_card_with_qty(driver, wait, "x1")
    assert card is not None
    print(f"Verified: {normalize_text(card.text)}")

    # --- Add 4 more (total x5) ---
    driver.get("http://localhost:5173/cards")
    search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Search']")))
    search_input.clear()
    search_input.send_keys("Connor Bedard\n")
    add_to_owned(driver, wait, "Connor Bedard", times=4)

    # --- Verify x5 ---
    driver.get("http://localhost:5173/owned")
    card = find_card_with_qty(driver, wait, "x5")
    assert card is not None
    print(f"Now shows: {normalize_text(card.text)}")

    # --- Remove 3 (to x2) ---
    card.click()
    remove_from_owned(driver, wait, 3)
    driver.get("http://localhost:5173/owned")
    card = find_card_with_qty(driver, wait, "x2")
    assert card is not None
    print(f"Now shows: {normalize_text(card.text)}")

    # --- Delete all ---
    card.click()
    remove_from_owned(driver, wait, 2)
    driver.get("http://localhost:5173/owned")
    empty = wait.until(
        EC.presence_of_element_located((By.XPATH, "//p[contains(text(), \"You don't own any cards\")]"))
    )
    assert empty.is_displayed()
    print("Collection is empty!")

    print("\nFINAL OWNED CARDS TEST → 100% PASSED")
