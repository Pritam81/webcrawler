import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from urllib.request import urlretrieve

# Get user input
query = input("Enter your search term: ")
num_images = 10000  # Number of images to fetch
search_url = f"https://www.google.com/search?q={quote(query)}&tbm=isch"

# Set headers to mimic a browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# Send request
response = requests.get(search_url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Create folder to save images
folder_name = query.replace(" ", "_")
os.makedirs(folder_name, exist_ok=True)

# Find image tags
img_tags = soup.find_all("img")
count = 0

for img_tag in img_tags:
    if count >= num_images:
        break
    img_url = img_tag.get("src")
    
    # Some images are base64, skip them
    if not img_url or img_url.startswith("data:"):
        continue
    
    try:
        img_path = os.path.join(folder_name, f"{query}_{count + 1}.jpg")
        urlretrieve(img_url, img_path)
        print(f"Downloaded image {count + 1}")
        count += 1
    except Exception as e:
        print(f"Could not download image {count + 1}: {e}")

print("Download completed.")