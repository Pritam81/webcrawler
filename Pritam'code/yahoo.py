import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException

def scrape_yahoo_images(query, num_images, download_path="downloaded_images"):
    # Prepare the URL
    base_url = "https://images.search.yahoo.com/search/images?p="
    search_url = base_url + query.replace(' ', '+')

    # Setup Selenium
    options = Options()
    options.add_argument('--headless')  # Remove this line if you want to see the browser
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)
    driver.get(search_url)
    time.sleep(3)

    # Scroll and click "Show more images" dynamically
    collected_images = set()

    while len(collected_images) < num_images:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        anchors = soup.find_all("a", class_="redesign-img round-img")

        for a in anchors:
            img = a.find("img")
            if img and img.get("src"):
                collected_images.add(img["src"])
                if len(collected_images) >= num_images:
                    break

        try:
            show_more_button = driver.find_element(By.CLASS_NAME, "more-res")
            show_more_button.click()
            time.sleep(2)
        except (NoSuchElementException, ElementClickInterceptedException):
            # No button or can't click, try to scroll
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

    driver.quit()

    # Download the images
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    print(f"Found {len(collected_images)} images. Downloading...")

    for idx, img_url in enumerate(list(collected_images)[:num_images]):
        try:
            img_data = requests.get(img_url, timeout=10).content
            with open(os.path.join(download_path, f"{query}_{idx+1}.jpg"), "wb") as f:
                f.write(img_data)
            print(f"Downloaded image {idx+1}")
        except Exception as e:
            print(f"Failed to download image {idx+1}: {e}")

    print("✅ Done!")

# Example usage:
if __name__ == "__main__":
    search_term = input("Enter image search term: ")
    num = int(input("Enter number of images to download: "))
    scrape_yahoo_images(search_term, num)
