import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import os
load_dotenv()
API_KEY = os.getenv("API_KEY")
class SearchTool:
    def __init__(self):
        self.name = "SearchTool"
        self.description = "A tool to search the web for financial information and extract text from PDFs."

    def run(self, query):
        processed_query = f"{query}:pdf"
        response = requests.get("https://serpapi.com/search", params={
            "q": query,
            "api_key": API_KEY,
            "num": 2
        })
        data = response.json()
        for result in data.get("organic_results", []):
            print(result["title"])
            print(result["link"])
            try: 
                pdf_response = requests.get(result["link"], timeout=30)
                content_type = pdf_response.headers.get("Content-Type", "")
                print(content_type)
                if "application/pdf" not in content_type:
                    print("The link does not point to a PDF file.")
                    continue
                else:
                    with open("data/raw/" + result["title"] + ".pdf", "wb") as f:
                        f.write(pdf_response.content)
                
                print("Successfully extracted text from PDF.")
            except Exception as e:
                print(f"Error processing PDF: {e}")
