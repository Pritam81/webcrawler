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

def get_all_image_srcs(driver, base_url, total_images):
    image_urls = set()
    page_number = 1
    scroll_pause_time = 2

    print("📜 Scraping image links across pages...")

    while len(image_urls) < total_images:
        page_url = base_url if page_number == 1 else f"{base_url.rstrip('/')}/page/{page_number}/"
        print(f"🌐 Visiting: {page_url}")
        driver.get(page_url)
        time.sleep(scroll_pause_time)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        picture_tags = soup.find_all("picture")

        new_images_found = 0

        for picture in picture_tags:
            img = picture.find("img")
            if img and img.get("class") == ["image"]:
                src = img.get("src")
                if src:
                    if src.startswith("//"):
                        src = "https:" + src
                    elif src.startswith("/"):
                        src = urljoin("https://picjumbo.com", src)
                    if src not in image_urls:
                        image_urls.add(src)
                        new_images_found += 1

            if len(image_urls) >= total_images:
                break

        if new_images_found == 0:
            print("⚠️ No new images found on this page. Stopping further scraping.")
            break

        page_number += 1

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
    base_search_url = f"https://picjumbo.com/search/{query.lower().replace(' ', '-')}/"
    image_urls = get_all_image_srcs(driver, base_search_url, total_images)
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
