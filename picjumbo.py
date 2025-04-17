import os
import time
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def get_all_image_srcs(driver, query, total_images):
    search_url = f"https://picjumbo.com/search/{query.lower().replace(' ', '-')}/"
    driver.get(search_url)
    image_urls = set()
    last_height = 0
    scroll_pause_time = 2

    print("📜 Scrolling and collecting image links...")

    while len(image_urls) < total_images:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        image_tags = soup.find_all("img", class_="image")

        for img in image_tags:
            src = img.get("src")
            if src:
                if src.startswith("//"):
                    src = "https:" + src
                elif src.startswith("/"):
                    src = urljoin("https://picjumbo.com", src)
                image_urls.add(src)

        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)

        # Check if page has stopped loading new content
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("📌 Reached end of page.")
            break
        last_height = new_height

    return list(image_urls)[:total_images]

def download_image(img_url, dest_folder, img_num):
    try:
        response = requests.get(img_url, stream=True)
        if response.status_code == 200:
            file_ext = os.path.splitext(img_url)[1].split('?')[0]
            if not file_ext:
                file_ext = ".jpg"
            filename = f"image_{img_num}{file_ext}"
            file_path = os.path.join(dest_folder, filename)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
    except Exception as e:
        print(f"❌ Error downloading {img_url}: {e}")

def scrape_picjumbo_images(query, total_images):
    dest_folder = f"picjumbo_{query.replace(' ', '_')}_images"
    os.makedirs(dest_folder, exist_ok=True)

    driver = init_driver()
    image_urls = get_all_image_srcs(driver, query, total_images)
    driver.quit()

    if not image_urls:
        print("❌ No image URLs found.")
        return

    print(f"✅ Found {len(image_urls)} image(s) for '{query}'")

    downloaded = 0
    for url in tqdm(image_urls, desc="📥 Downloading Images"):
        if downloaded >= total_images:
            break
        download_image(url, dest_folder, downloaded + 1)
        downloaded += 1

    print(f"\n🎉 Successfully downloaded {downloaded} image(s) into '{dest_folder}'")

# ==== Main ====
if __name__ == "__main__":
    query = input("Enter image search keyword: ")
    total_images = int(input("Enter total number of images to download: "))
    scrape_picjumbo_images(query, total_images)
