from dataclasses import dataclass

@dataclass
class Patent:
    id: str
    title: str
    summary: str
    relevance_score: float = 0.0

######### Nick to paste new GPatentEngine implementation


from anthropic import Anthropic
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from typing import Any

import os
import re
import requests

log = print


# id, title, summary, relevance_score


class GPatentEngine:
    def __init__(self, do_multiplex=False, max_elems=5):
        self.do_multiplex = do_multiplex
        self.max_elems = max_elems
        # Set up the Chrome WebDriver
        options = Options()
        options.add_argument("--headless=new")
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(driver=self.driver, timeout=5)

        self.client = Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
        )

    def _selenium_patent_search(self,
                                destination,
                                wait_fn,
                                fetch_fn,
                                process_fn):
        self.driver.get(destination)
        try:
            wait_fn()
        except Exception as e:
            log(f"Wait function raised {e}, so aborting this search branch.")
            return []

        # Parse through search results as they load
        previous_count = 0
        while True:
            # Get all currently loaded search result elements
            results = fetch_fn()

            # We're done? Exit loop
            if len(results) == previous_count:
                break

            # Process newly loaded elements
            for result in results[previous_count:]:
                try:
                    process_fn(result)
                except Exception as e:
                    log(f"Encountered error when parsing patent results: {e}")

            previous_count = len(results)

            # Scroll to bottom to trigger more results [optional]
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def _patent_direct_search(self, query: str) -> list[str]:
        target = "https://patents.google.com/"

        if len(query.strip().split()) > 20:
            claude_output = self.client.messages.create(
                messages=[
                    {
                        "role": "user",
                        "content": f"Please summarize the following text in 20 words as accurately as possible. You get $100 for not introducing any inaccuracies.\nTEXT: {query}"
                    }
                ],
                model="claude-3-7-sonnet-latest",
                max_tokens=1028
            )

            query = claude_output.content[0].text

        def _wait_for_search_box(driver, wait):
            wait.until(EC.presence_of_element_located((By.NAME, "q")))
            search_box = driver.find_element(By.NAME, "q")  # the input box uses name="q"
            # Execute the search
            search_box.send_keys(query)
            search_box.send_keys(Keys.RETURN)
            # Wait for the first batch to load
            wait.until(EC.presence_of_element_located(
                (By.XPATH, "//article[contains(@class, 'search-result-item')]/following::a[1]")))

        def _fetch_results(driver) -> list[Any]:
            return driver.find_elements(By.XPATH, "//state-modifier[contains(@class, 'search-result-item')]")

        patents = []

        def _process_fn(result) -> None:
            patents.append(result.get_attribute('data-result').split("/")[1])

        self._selenium_patent_search(destination=target,
                                     wait_fn=partial(_wait_for_search_box, driver=self.driver, wait=self.wait),
                                     fetch_fn=partial(_fetch_results, driver=self.driver),
                                     process_fn=_process_fn)

        return patents

    def _patent_internet_search(self, query: str) -> list[str]:
        target = "https://www.duckduckgo.com/"

        def _wait_for_search_box(driver, wait):
            wait.until(EC.presence_of_element_located((By.NAME, "q")))
            search_box = driver.find_element(By.NAME, "q")  # the input box uses name="q"
            # Execute the search
            search_box.send_keys(f"{query} site:patents.google.com")
            search_box.send_keys(Keys.RETURN)
            # Wait for the first batch to load
            wait.until(EC.presence_of_element_located((By.XPATH, "//article[@data-nrn='result']")))

        def _fetch_results(driver) -> list[Any]:
            return driver.find_elements(By.XPATH, "//article[@data-nrn='result']//a")

        patents = []

        def _process_fn(result) -> None:
            link_value = result.get_attribute("href")
            if link_value and link_value.startswith("https://patents.google.com"):
                patent = re.match(r".*/patent/(.*)/.*", link_value)
                if patent and patent.group(1) is not None:
                    patents.append(patent.group(1))

        self._selenium_patent_search(destination=target,
                                     wait_fn=partial(_wait_for_search_box, driver=self.driver, wait=self.wait),
                                     fetch_fn=partial(_fetch_results, driver=self.driver),
                                     process_fn=_process_fn)
        return patents

    def _patent_fpo_search(self, query: str) -> list[str]:
        target = "https://www.freepatentsonline.com/"

        def _wait_for_search_box(driver, wait):
            wait.until(EC.presence_of_element_located((By.NAME, "query_txt")))
            search_box = driver.find_element(By.NAME, "query_txt")  # the input box uses name="q"
            # Execute the search
            search_box.send_keys(f"{query}")
            search_box.send_keys(Keys.RETURN)
            # Wait for the first batch to load
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "listing_table")))

        def _fetch_results(driver) -> list[Any]:
            return driver.find_elements(By.XPATH, "//td[contains(@width, '15%')]")[:self.max_elems]

        patents = []

        def _process_fn(result) -> None:
            patent_no = result.text.strip().upper()
            if not patent_no.startswith("US"):
                patent_no = "US" + patent_no
            patents.append(patent_no)

        self._selenium_patent_search(destination=target,
                                     wait_fn=partial(_wait_for_search_box, driver=self.driver, wait=self.wait),
                                     fetch_fn=partial(_fetch_results, driver=self.driver),
                                     process_fn=_process_fn)
        return patents

    def _search(self, query: str) -> list[str]:
        patents: set[str] = set()

        # ** Google is detecting us as bots, sad. Deal with this later. **
        # for patent_candidate in self._patent_direct_search(query):
        #     if patent_candidate not in patents:
        #         patents.add(patent_candidate)

        for patent_candidate in self._patent_fpo_search(query):
            if patent_candidate not in patents:
                patents.add(patent_candidate)
        # for patent_candidate in self._patent_internet_search(query):
        #     if patent_candidate not in patents:
        #         patents.add(patent_candidate)

        with ThreadPoolExecutor(max_workers=20) as executor:
            allowlist = list(executor.map(partial(self.is_prior_art, query), patents))

        return [self.id_to_patent(query, patent_id) for patent_id, is_prior_art in zip(patents, allowlist) if
                is_prior_art]

    def search(self, query: str) -> list[str]:
        prompts = self._multiplex(query)

        patents = []
        for prompt in prompts:
            patents.extend(self._search(prompt))

        return list(set(patents))

    def _multiplex(self, query: str, count=5) -> list[str]:
        if not self.do_multiplex:
            return [query]

        def rephrase():
            claude_output = self.client.messages.create(
                system="You are an assistant for a patent law firm helping a client do prior art discovery for a patent they are interested in pursuing. Please rephrase their idea to be as clear and brief as possible so that our interns don't make any mistakes while researching. State **ONLY** the idea and no other commentary.",
                messages=[
                    {
                        "role": "user",
                        "content": f"IDEA: {query}",
                    }
                ],
                model="claude-3-7-sonnet-latest",
                max_tokens=1024,
            )
            return claude_output.content[0].text

        with ThreadPoolExecutor(max_workers=count) as executor:
            futures = [executor.submit(rephrase) for _ in range(count)]
            results = [f.result() for f in futures]

        return [query] + results

    def is_prior_art(self, idea, patent_id):
        # patent_claim_dict = self.get_patent_claims(patent_id)
        # claude_output = self.client.messages.create(
        #     system="You are an assistant for a patent law firm helping a client do prior art discovery for a patent they are interested in pursuing. Given their proposed idea and a description of another patent someone in the firm found during discovery, determine whether the patent is related at all to the idea. Return either true or false only.",
        #     messages=[
        #         {
        #             "role": "user",
        #             "content": f"IDEA: {idea}\nPATENT: {patent_claim_dict}",
        #         }
        #     ],
        #     model="claude-3-7-sonnet-latest",
        #     max_tokens=8192,
        # )

        # raw_output = claude_output.content[0].text
        # # Don't omit if output is malformed, so != false rather than == true
        # return raw_output.strip().lower() != 'false'
        # Clause is **quite** aggressive here. Tune later.
        return True

    def calculate_relevance_score(self, idea, summary):
        claude_output = self.client.messages.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Please calculate a relevance score between 0 and 1 between the idea and the patent. Provide only the score and no other commentary. IDEA: {idea}\nPATENT: {summary}",
                }
            ],
            model="claude-3-7-sonnet-latest",
            max_tokens=8192,
        )

        raw_output = claude_output.content[0].text
        try:
            return float(raw_output.strip())
        except (ValueError, TypeError):
            return 0.0

    def get_patent_summary(self, props):
        claude_output = self.client.messages.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Summarize this patent into 100 english words or fewer:\n{props}",
                }
            ],
            model="claude-3-7-sonnet-latest",
            max_tokens=8192,
        )

        return claude_output.content[0].text

    def id_to_patent(self, idea, patent_id) -> dict[str, Any]:
        props = self.get_patent_claims(patent_id)
        summary = self.get_patent_summary(props)
        return {
            "id": patent_id,
            "title": props.get("title", "N/A"),
            "summary": summary,
            "relevance_score": self.calculate_relevance_score(idea, summary),
        }

    @staticmethod
    def get_gpatent_claims(patent_id) -> dict[str, str]:
        url = f"https://patents.google.com/patent/{patent_id}/en"
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        print(resp.text)

        return {
            "title": soup.find('h1', id="title").text,
            "abstract": getattr(soup.find('div', class_='abstract'), "text", ""),
            "claims": [claim.text for claim in soup.find_all(class_='claim-text')]
        }

    @staticmethod
    def get_patent_claims(patent_id) -> dict[str, str]:
        url = f"https://freepatentsonline.com/{patent_id}.html"
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        title = soup.find('div', string="Title:").find_next_sibling('div').text
        if title is not None:
            title = title.strip()

        abstract = soup.find('div', string='Abstract:').find_next_sibling('div').text
        if abstract is not None:
            abstract = abstract.strip()

        claims = soup.find('div', string="Claims:").find_next_sibling('div').text
        if claims is not None:
            claims = claims.strip()

        return {
            "title": title,
            "abstract": abstract,
            "claims": claims,
        }


##### End nick code paste

# Start controller code

from typing import List

"""
1. Analyze Input: Use LLM to take in description and produce keywords
2. Search Arxiv: Currently using python library
3. Analyze Papers: Use LLM to analyze papers and return the most relevant ones
"""
async def search_patents_by_description(description: str) -> List[Patent]:
    engine = GPatentEngine()
    try:
        patent_dicts = engine.search(description)
    finally:
        engine.driver.quit()

    # TODO convert patent IDs to actual values
    patent_dicts = [p for p in patent_dicts if p['relevance_score'] > 0]
    patent_dicts.sort(key=lambda dct: dict['relevance_score'], reverse=True)

    patents = [Patent(id=p['id'], title=p['title'], summary=p['summary'], relevance_score=p['relevance_score']) for p in patent_dicts]
    return patents


# Let's test the search patents by description code here
# if __name__ == "__main__":
#     import asyncio
    
#     test_description = "A method for using machine learning to automatically detect and classify different types of birds from audio recordings of their songs"
    
#     async def run_test():
#         results = await search_patents_by_description(test_description)
#         print(f"Found {len(results)} potentially relevant patents:")
#         for patent_id in results:
#             print(f"- {patent_id}")
    
#     asyncio.run(run_test())