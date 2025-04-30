import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm
from urllib.parse import quote

# ========== USER INPUT ==========
query = input("🔍 Enter image search term: ")
num_images = int(input("🖼️ Enter number of images to download: "))

# ========== SETUP ==========
output_dir = f"images_{query.replace(' ', '_')}"
os.makedirs(output_dir, exist_ok=True)

chrome_options = Options()
chrome_options.add_argument("--headless")  # comment this if you want to see browser
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")

driver = webdriver.Chrome(options=chrome_options)
search_url = f"https://images.search.yahoo.com/search/images?p={quote(query)}"
driver.get(search_url)

image_urls = set()
last_height = driver.execute_script("return document.body.scrollHeight")
scroll_pause = 2
retry_limit = 3
retry_count = 0

print("📜 Scrolling and collecting image URLs...")

# ========== SCROLL & COLLECT ==========
while len(image_urls) < num_images and retry_count < retry_limit:
    # Scroll down
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(scroll_pause)

    # Explicitly find and click the "Show more images" button if present
    try:
        show_more_button = driver.find_element(By.CLASS_NAME, "more-res")
        if show_more_button.is_displayed():
            driver.execute_script("arguments[0].click();", show_more_button)
            print("🔘 Clicked 'Show more images' button.")
            time.sleep(2)
    except Exception as e:
        pass  # No button to click or error occurred

    # Collect image URLs
    thumbnails = driver.find_elements(By.CLASS_NAME, "round-img")
    for thumb in thumbnails:
        try:
            img = thumb.find_element(By.TAG_NAME, "img")
            src = img.get_attribute("src")
            if src and src.startswith("http"):
                image_urls.add(src)
        except:
            continue

    print(f"🔗 Collected {len(image_urls)} image links...")

    # Detect if page stopped growing
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        retry_count += 1
    else:
        retry_count = 0
    last_height = new_height

driver.quit()

# ========== DOWNLOAD ==========
download_count = min(num_images, len(image_urls))
print(f"\n📥 Downloading {download_count} images...\n")

for i, url in enumerate(tqdm(list(image_urls)[:download_count], desc="Downloading")):
    try:
        response = requests.get(url, timeout=10)
        with open(os.path.join(output_dir, f"{query.replace(' ', '_')}_{i+1}.jpg"), "wb") as f:
            f.write(response.content)
    except Exception as e:
        tqdm.write(f"[!] Failed to download {url[:50]}... Reason: {e}")

print(f"\n✅ Done! Saved {download_count} images to: {output_dir}")