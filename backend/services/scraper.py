import requests
from bs4 import BeautifulSoup
import re

class JobScraper:
    @staticmethod
    def scrape_url(url: str) -> dict:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.decompose()
                
            text = soup.get_text(separator=' ')
            
            # Clean text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Basic metadata extraction (very heuristic)
            title = soup.title.string if soup.title else "Unknown Role"
            
            return {
                "title": title.strip(),
                "description": clean_text[:5000], # Limit length
                "url": url
            }
        except Exception as e:
            raise Exception(f"Failed to scrape URL: {str(e)}")
