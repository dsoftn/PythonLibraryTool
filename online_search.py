from bs4 import BeautifulSoup as bs
import requests
import googlesearch
import urllib.request


class OnlineSearch():
    """Tries to find documentation and code examples for the requested object.
    The accuracy of the results is not guaranteed.
    """
    
    def __init__(self, full_object_name: str = ""):
        
        self._full_object_name = full_object_name
        
        # self._code_urls = list of URLs from search engine that contains code examples
        # Item in list = [title(str), description(str)]
        self._code_urls = []
        
        self._doc_urls = []  # List of URLs from google for documentation

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

    def _google_search_for_code(self, site_url: str = ""):
        """Performs a google search for code examples for the requested object.
        If the site_url parameter is passed, the search is performed only on that site.
        Args:
            site_url (str): Searches on this site only
        Return:
            None: Creates self._code_urls list
        """
        self._code_urls = []
        search_string = self._make_code_search_url()
        if site_url:
            if site_url.find("site:") >= 0:
                search_string = f"{site_url} {search_string}"
            else:
                search_string = f"site:{site_url} {search_string}"
        urls = googlesearch.search(search_string, 1)
        for url in urls:
            self._code_urls.append(url)
        if not self._code_urls:
            self._error_message = "Google did not find any results for the requested search."

    def _bing_search_for_code(self, site_url: str = ""):
        """Performs a www.bing.com search for code examples for the requested object.
        If the site_url parameter is passed, the search is performed only on that site.
        Args:
            site_url (str): Searches on this site only
        Return:
            None: Creates self._code_urls list
        """

        # Following code is valid if i have web page source in html var
        # urls = self._bing_find_urls(html)
        # descs = self._bing_find_descriptions(html)
        # for idx, data in enumerate(urls):
        #     self._code_urls.append(data, descs[idx])
        #     print (data, "\n", descs[idx])
        #
        # if not self._code_urls:
        #     self._error_message = "Bing did not find any results for the requested search."
        pass

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

    def _bing_find_urls(self, html: str) -> list:
        """Searches for urls in html
        Return
            list: Url strings
        """
        urls = []
        url_pos = 0
        url_search = '<ol id="b_results" class=""><li class="b_algo"><h2><a href="'
        url_string = ""
        
        while url_pos >= 0:
            url_pos = html.find(url_search, url_pos)
            if url_pos >=0:
                first_quota = html.find('"', url_pos)
                second_quota = html.find('"', first_quota + 1)
                url_string = html[first_quota:second_quota]
                urls.append(url_string)
                url_pos +=1

        return urls

    def _bing_find_descriptions(self, html: str) -> list:
        """Searches for descriptions in html
        Return
            list: Descriptions strings
        """
        descs = []
        desc_pos = 0
        desc_search = "</span>&nbsp;&#0183;&#32;"
        desc_end_search = "</p></div>"
        desc_string = ""
        
        while desc_pos >= 0:
            desc_pos = html.find(desc_search, desc_pos)
            if desc_pos >=0:
                d_end = html.find(desc_end_search, desc_pos)
                tmp = html[desc_pos:d_end].split(";&")
                tmp2 = tmp[-1]
                desc_string = tmp2[tmp2.find(";") + 1:]
                descs.append(desc_string)
                desc_pos +=1

        return descs

    def _make_code_search_url(self) -> str:
        """Creates a search string that will be forwarded to google.com and used to find
        sample code for the requested object.
        Returns:
            (str): Search string
        """
        full_object_name = self._full_object_name.replace(".", " ")
        result = f"Python code example {full_object_name}"
        return result

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

    def get_code_examples_geeks_for_geeks(self, url: str) -> list:
        """Returns sample code from the requested url.
        Use the url provided by the search engine.
        Returns:
            list: [code_title, code_text]
        """        
        # Get url content
        html_text = requests.get(url).content
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

    def stackoverflow(self):
        SITE = StackAPI("stackoverflow")
        SITE.page_size = 50
        SITE.max_pages = 1
        answers = SITE.fetch("answers", q = "LineEdit PyQt5")

        with open("stack.txt", "w", encoding="utf-8") as file:
            for answer in answers["items"]:
                try:
                    json.dump(answer, file)
                except:
                    print ("ERROR IN SAVING FILE")
                print (answer)
                print (answer["body"])

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