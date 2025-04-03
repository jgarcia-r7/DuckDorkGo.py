# DuckDorkGo.py
A DuckDuckGo powered dorking script to scrape files, download them, and extract metadata.

### Notes
Was tired of google dorking scripts not working too damn often, so duckduckgo it is.
For reliability (lol), uses selenium with chromium-driver to browse duckduckgo, scroll through the results, etc.  
Anyways, you run it against a domain, it scrapes for the filetypes specified (common ones set by default), downloads all of em, extracts useful metadata, and makes you a nice simple CSV - yes for report simplicity.

### Setup
Install Chromium/Chromium driver:
```bash
sudo apt update; sudo apt install chromium chromium-driver
```
Clone the repo, install pip packages, run it:
```bash
git clone https://github.com/jgarcia-r7/DuckDorkGo.py
cd DuckDorkGo.py/
python3 -m venv .ddg
source .ddg/bin/activate
pip3 install -r requirements.txt
python3 DuckDorkGo.py [domain.com]
```
### Usage
`-h` output:  
```bash
usage: duckdorkgo.py [-h] [-m MAX_RESULTS] [-f FILETYPES [FILETYPES ...]] [--proxy PROXY] domain

DuckDuckGo File Dorker (Selenium + Metadata)

positional arguments:
  domain                Target domain (e.g., domain.com)

options:
  -h, --help            show this help message and exit
  -m, --max-results MAX_RESULTS
                        Max number of file URLs to find
  -f, --filetypes FILETYPES [FILETYPES ...]
                        Filetypes to include
  --proxy PROXY         Proxy server (e.g., socks5://127.0.0.1:9050)
```

### Example
Scraping for **300** max results on **usda.gov**:  
`python3 DuckDorkGo.py usda.dov -m 300`  
![image](https://github.com/user-attachments/assets/bae2f47c-ff20-4065-95c3-f30b847d2126)

Scraping **example.com** for pdf and docx files with a maximum of 100 results:  
`python3 DuckDorkGo.py example.com -f pdf docx -m 100`
