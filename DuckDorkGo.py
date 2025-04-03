# DuckDorkGo.py
# A DuckDuckGo powered dorking script to scrape files, download them, and extract metadata.
# github.com/jgarcia-r7

import os
import time
import shutil
import argparse
import pandas as pd
from pathlib import Path
from urllib.parse import quote_plus
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from docx import Document
import olefile

# Default filetypes, add or change if you want
FILETYPES = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']

# Chromedriver stuff, damn pita is what it is
def setup_driver(proxy=None):
    chromedriver_path = shutil.which("chromedriver")
    if not chromedriver_path:
        print("\033[1;31m[!]\033[0m chromedriver not found in PATH.")
        print("\033[1;31m[!]\033[0m Please install it or add it to your PATH (e.g., /usr/bin or ~/bin).")
        print("\033[1;31m[!]\033[0m For Kali Linux: sudo apt install chromium-driver")
        exit(1)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36")

    if proxy:
        chrome_options.add_argument(f"--proxy-server={proxy}")

    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Scrape function
def scrape_duckduckgo(domain, filetypes, max_results=100, proxy=None):
    query = f"site:{domain} ({' OR '.join(f'filetype:{ft}' for ft in filetypes)})"
    base_url = "https://duckduckgo.com/?q=" + quote_plus(query) + "&ia=web"

    driver = setup_driver(proxy=proxy)
    results = set()

    print(f"\033[1;33m[!]\033[0m Starting DuckDuckGo scraping for max {max_results} results...")

    driver.get(base_url)
    time.sleep(2)

    scroll_pause = 2
    last_height = driver.execute_script("return document.body.scrollHeight")

    while len(results) < max_results:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        links = soup.find_all("a", href=True)

        new_results = 0
        for link in links:
            href = link['href']
            if any(href.lower().endswith(f'.{ext}') for ext in filetypes):
                if href not in results:
                    results.add(href)
                    new_results += 1
            if len(results) >= max_results:
                break

        print(f"\033[1;32m[+]\033[0m Collected: {len(results)} results so far")

        if len(results) >= max_results:
            break

        try:
            more_button = driver.find_element(By.ID, "more-results")
            driver.execute_script("arguments[0].scrollIntoView(true);", more_button)
            time.sleep(1)
            more_button.click()
            time.sleep(scroll_pause)
        except Exception:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("\033[1;31m[!]\033[0m No more results loaded after scrolling.")
            break
        last_height = new_height

    driver.quit()
    return sorted(results)

# download all the files because we need to download all the files
def download_files(urls, domain):
    out_dir = Path("downloads") / domain
    out_dir.mkdir(parents=True, exist_ok=True)
    url_map = {}

    for url in urls:
        filename = os.path.basename(url.split("?")[0])
        out_path = out_dir / filename
        url_map[filename] = url
        if out_path.exists():
            print(f"\033[1;90m[-]\033[0m Skipping (exists): {filename}")
            continue
        try:
            print(f"\033[1;32m[+]\033[0m Downloading: {filename}")
            os.system(f'curl -sL "{url}" -o "{out_path}"')
        except Exception as e:
            print(f"\033[1;31m[!]\033[0m Error downloading {url}: {e}")

    return url_map

# well yeah
def extract_metadata(domain, url_map):
    download_path = Path(f"downloads/{domain}")
    metadata_results = []

    def extract_pdf_metadata(filepath):
        try:
            reader = PdfReader(filepath)
            meta = reader.metadata
            return {
                "Author": meta.author,
                "Creator": meta.creator,
                "Producer": meta.producer,
                "Subject": meta.subject,
                "Title": meta.title
            }
        except:
            return {}

    def extract_docx_metadata(filepath):
        try:
            doc = Document(filepath)
            props = doc.core_properties
            return {
                "Author": props.author,
                "Title": props.title,
                "Subject": props.subject,
                "Last Modified By": props.last_modified_by,
                "Keywords": props.keywords
            }
        except:
            return {}

    def extract_ole_metadata(filepath):
        try:
            if olefile.isOleFile(filepath):
                ole = olefile.OleFileIO(filepath)
                meta = ole.get_metadata()
                return {
                    "Author": meta.author,
                    "Title": meta.title,
                    "Subject": meta.subject,
                    "Last Saved By": meta.last_saved_by,
                    "Creating Application": meta.creating_application
                }
        except:
            return {}

    for file in download_path.glob("*"):
        ext = file.suffix.lower()
        if ext == ".pdf":
            meta = extract_pdf_metadata(file)
        elif ext == ".docx":
            meta = extract_docx_metadata(file)
        elif ext in [".doc", ".xls", ".ppt"]:
            meta = extract_ole_metadata(file)
        else:
            continue

        if meta:
            metadata_results.append({
                "File": file.name,
                "Source URL": url_map.get(file.name, "Unknown"),
                **{k: v for k, v in meta.items() if v}
            })

    if metadata_results:
        df = pd.DataFrame(metadata_results)
        output_path = download_path / "metadata_report.csv"
        df.to_csv(output_path, index=False)
        print(f"\033[1;35m[*]\033[0m Metadata report saved to: {output_path}")
    else:
        print("\033[1;90m[-]\033[0m No useful metadata found.")

# mainframestuff
def main():
    print("\033[1;37mDuckDorkGo.py\033[0m - by \033[1;36mjgarcia-r7\033[0m\n")
    parser = argparse.ArgumentParser(description="DuckDuckGo File Dorker and Metadata Extractor")
    parser.add_argument("domain", help="Target domain (e.g., domain.com)")
    parser.add_argument("-m", "--max-results", type=int, default=100, help="Max number of file URLs to find")
    parser.add_argument("-f", "--filetypes", nargs="+", default=FILETYPES, help="Filetypes to include")
    parser.add_argument("--proxy", help="Proxy server (e.g., socks5://127.0.0.1:9050)")
    args = parser.parse_args()

    print(f"\033[1;36m[+]\033[0m Domain: {args.domain}")
    print(f"\033[1;36m[+]\033[0m Filetypes: {', '.join(args.filetypes)}")
    print(f"\033[1;36m[+]\033[0m Max Results: {args.max_results}")
    if args.proxy:
        print(f"\033[1;36m[+]\033[0m Using Proxy: {args.proxy}")

    urls = scrape_duckduckgo(args.domain, args.filetypes, args.max_results, proxy=args.proxy)

    if urls:
        print(f"\033[1;32m[+]\033[0m Found {len(urls)} document URLs")
        url_map = download_files(urls, args.domain)
        extract_metadata(args.domain, url_map)
    else:
        print("\033[1;31m[-]\033[0m No documents found.")


if __name__ == "__main__":
    main()
