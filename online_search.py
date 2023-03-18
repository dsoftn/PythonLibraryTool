from bs4 import BeautifulSoup as bs
import requests
import urllib.request


class OnlineSearch():
    """Tries to find documentation and code examples for the requested object.
    The accuracy of the results is not guaranteed.
    """
    
    def __init__(self, full_object_name: str = ""):
        
        self._full_object_name = full_object_name
        
        self._code_urls = []  # List of URLs from duckduckgo for code examples
        
        self._doc_urls = []  # List of URLs from duckduckgo for documentation

        self._error_message = ""  # Message that method 'get_error_message' returns
    
    def get_full_object_name(self):
        """Returns full_object_name string
        """
        return self._full_object_name
    
    def set_full_object_name(self, full_object_name: str):
        """Sets full_object_name string value.
        If a new value is passed, set lists with codes, descriptions and urls to empty.
        """
        if self._full_object_name != full_object_name:
            self._code_urls = []
            self._doc_urls = []
            
        self._full_object_name = full_object_name
    
    def search_documentation(self):
        pass

    def get_error_message(self):
        """Returns a message about the error that occurred, if there is no error returns
         an empty string.
        """
        if self._error_message:
            result = self._error_message
            self._error_message = ""
            return result
        else:
            return ""

    def _duck_search_for_code(self, site_url: str = ""):
        """Performs a duckduckgo.com search for code examples for the requested object.
        If the site_url parameter is passed, the search is performed only on that site.
        Args:
            site_url (str): Searches on this site only
        Return:
            None: Creates self._code_urls list
        """

        self._code_urls = []
        # Define Duck url
        url = f"https://lite.duckduckgo.com/lite/search?q=site%3A+{site_url}+Python+code+example+{self._full_object_name.replace('.', '+')}"
        # Get Duck search page source code
        result_page = urllib.request.urlopen(url)
        html = result_page.read().decode("utf-8")
        # Parse html with BeautifulSoup
        soup = bs(html, "lxml")
        urls = []
        # Find all urls and add them to list
        results = soup.find_all("span", class_="link-text")
        for result in results:
            result_text = result.text.strip()
            if result_text[:4].lower() != "http":
                result_text = "https://" + result_text
            urls.append(result_text)
        descriptions = []
        # Find all descriptions and add them to list
        results = soup.find_all("td", class_="result-snippet")
        for result in results:
            descriptions.append(result.text.strip())
        # Create self.code_urls list
        for idx, item in enumerate(urls):
            if idx < len(descriptions):
                self._code_urls.append([item, descriptions[idx]])
            else:
                self._code_urls.append([item, ""])
        if not self._code_urls:
            self._error_message = "Duck did not find any results for the requested search."

    def get_search_results_for_code_examples_geeks_for_geeks(self, full_object_name: str = ""):
        """It searches the site 'www.geeksforgeks.org' trying to find code examples
         for the requested object.
         Search engine: www.duckduckgo.com
         Returns:
            list: list of code examples [title (str), text (str)]
         """

        if self._full_object_name != full_object_name and full_object_name != "":
            self.set_full_object_name(full_object_name)
        
        site = "www.geeksforgeeks.org"
        # Search with Duck
        if not self._code_urls:
            self._duck_search_for_code(site_url=site)
            if not self._code_urls:
                return
        return self._code_urls

    def get_search_results_for_docs(self, full_object_name: str = ""):
        """It searches online trying to find documentation for the requested object.
         Search engine: www.duckduckgo.com
         Returns:
            list: list of urls [url (str), description (str)]
         """

        if self._full_object_name != full_object_name and full_object_name != "":
            self.set_full_object_name(full_object_name)
        
        # Search with Duck
        if not self._doc_urls:
            self._duck_search_for_doc()
            if not self._doc_urls:
                return
        
        self._sort_doc_urls_by_relevance()
        
        return self._doc_urls

    def _sort_doc_urls_by_relevance(self):
        full_name_list = [x.strip() for x in self._full_object_name.split(".") if x !=""]
        if not full_name_list:
            return
        relevant = full_name_list[0]
        new_doc = []
        # Find result on https://pypi.org/
        for idx, item in enumerate(self._doc_urls):
            url = item[0].lower()
            if url.find(relevant) >= 0 and url.find("pypi.org") >= 0:
                new_doc.append(item)
                self._doc_urls.pop(idx)
                break
        # Find result on https://docs.python.org/
        for idx, item in enumerate(self._doc_urls):
            url = item[0].lower()
            if url.find(relevant) >= 0 and url.find("python.org") >= 0:
                new_doc.append(item)
                self._doc_urls.pop(idx)
                break
        # Find result on other site
        for idx, item in enumerate(self._doc_urls):
            url = item[0].lower()
            if url.find(relevant) >= 0 and url.find("python") < 0 and url.find("pypi") < 0:
                new_doc.append(item)
                self._doc_urls.pop(idx)
                break
        # Show first result on https://pypi.org/
        for idx, item in enumerate(self._doc_urls):
            url = item[0].lower()
            if url.find("pypi.org") >= 0:
                new_doc.append(item)
                self._doc_urls.pop(idx)
                break
        # Show first result on https://docs.python.org/
        for idx, item in enumerate(self._doc_urls):
            url = item[0].lower()
            if url.find("python.org") >= 0:
                new_doc.append(item)
                self._doc_urls.pop(idx)
                break
        # Show links that contains <relevant> in url
        for idx, item in enumerate(self._doc_urls):
            url = item[0].lower()
            if url.find(relevant) >= 0:
                new_doc.append(item)
                self._doc_urls.pop(idx)
        # Add other results
        for i in self._doc_urls:
            new_doc.append(i)
        
        self._doc_urls = []
        self._doc_urls = new_doc

    def _duck_search_for_doc(self):
        """Performs a duckduckgo.com search for documentation for the requested object.
        If the site_url parameter is passed, the search is performed only on that site.
        Return:
            None: Creates self._doc_urls list
        """

        self._doc_urls = []
        # Define Duck url
        url = f"https://lite.duckduckgo.com/lite/search?q=python+{self._full_object_name.replace('.', '+')}+documentation+pypi.org+docs.python.org"
        # Get Duck search page source code
        result_page = urllib.request.urlopen(url)
        html = result_page.read().decode("utf-8")
        # Parse html with BeautifulSoup
        soup = bs(html, "lxml")
        urls = []
        # Find all urls and add them to list
        results = soup.find_all("span", class_="link-text")
        for result in results:
            result_text = result.text.strip()
            if result_text[:4].lower() != "http":
                result_text = "https://" + result_text
            urls.append(result_text)
        descriptions = []
        # Find all descriptions and add them to list
        results = soup.find_all("td", class_="result-snippet")
        for result in results:
            descriptions.append(result.text.strip())
        # Create self.doc_urls list
        for idx, item in enumerate(urls):
            if idx < len(descriptions):
                self._doc_urls.append([item, descriptions[idx]])
            else:
                self._doc_urls.append([item, ""])
        if not self._doc_urls:
            self._error_message = "Duck did not find any results for the requested search."

    def get_code_examples_geeks_for_geeks(self, url: str) -> list:
        """Returns sample code from the requested url.
        Use the url provided by the search engine.
        Returns:
            list: [code_title, code_text]
        """        
        # Get url content
        try:
            html_text = requests.get(url).content
        except Exception as e:
            print ("Error: ", str(e))
            return [[]]
        # Parse html
        soup = bs(html_text, "lxml")
        # Create containers - each container contains one code example
        containers = soup.find_all("td", class_="code")
        # Append each code to self.code_examples_list
        count = 1
        code_text = ""
        code_examples = []  # List of code examples, [title (str), text (str)]
        for container in containers:
            code_block = container.select("div.line")
            for code_line in code_block:
                line = code_line.getText().replace("\xa0", " ")+"\n"
                code_text = code_text + line
            code_examples.append([f"Code Example ({str(count)})", code_text])
            count += 1
        return code_examples

    def run(self):
        # Primer koristenja
        html_text = requests.get(url).text
        
        soup = bs(html_text, "lxml")
        jobs =  soup.find_all("li", class_ = "clearfix job-fx")
        for job in jobs:
            company_name = job.find("h3", class_ = "joblist comp-name")
            skills = job.find("span", class_ = "srp-skills")
            job_info_url = job.header.h2.a["href"]
    

if __name__ == "__main__":
    tmp = OnlineSearch("nn")
    tmp._duck_search_for_code()