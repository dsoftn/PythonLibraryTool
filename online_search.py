from bs4 import BeautifulSoup as bs
import requests
import urllib.request
import lxml.html
import html


class OnlineSearch():
    """Tries to find documentation and code examples for the requested object.
    The accuracy of the results is not guaranteed.
    """
    
    def __init__(self, full_object_name: str = ""):
        
        self._full_object_name = full_object_name
        
        self._code_urls = []  # List of URLs from duckduckgo for code examples
        
        self._doc_urls = []  # List of URLs from duckduckgo for documentation

        self._error_message = ""  # Message that method 'get_error_message' returns
    
    def delete_code_search_results(self):
        self._code_urls = []
    
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
        if site_url:
            url = f"https://lite.duckduckgo.com/lite/search?q=site%3A+{site_url}+Python+code+example+{self._full_object_name.replace('.', '+')}"
        else:
            url = f"https://lite.duckduckgo.com/lite/search?q=Python+code+example+{self._full_object_name.replace('.', '+')}"
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

    def get_search_results_for_code_examples(self, full_object_name: str = "", site: str = ""):
        """It searches the site 'www.geeksforgeks.org' trying to find code examples
         for the requested object.
         Search engine: www.duckduckgo.com
         Returns:
            list: list of code examples [title (str), text (str)]
         """

        if self._full_object_name != full_object_name and full_object_name != "":
            self.set_full_object_name(full_object_name)
        
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

    def get_code_examples_all(self, url: str) -> list:
        """Returns sample code from the requested url.
        Use the url provided by the search engine.
        Returns:
            list: [code_title, code_text]
        """
        # For GeeksForGeeks call specific function
        # if url.find("www,geeksforgeeks.org") >= 0:
        #     result = self.get_code_examples_geeks_for_geeks(url)
        #     return result
        # Get url content
        try:
            html_text = requests.get(url).text
        except Exception as e:
            print ("Error: ", str(e))
            return [[]]

        html_text = html_text.replace("\t", "    ")
        # html_text = html.unescape(html_text)

        with open("test.txt", "w", encoding="utf-8") as file:
            file.write(html_text)

        html_text = self._fix_html(url, html_text)

        # Parse html
        container_delimiters = [['class="code', ''],
                                ['class=code>', ''],
                                ['class="codeblock">', ''],
                                ['class="code-block', ''],
                                ['class="program_box">', ''],
                                ['class="crayon-code">', ''],
                                ['class="kj kk kl km gt lq lr ls lt aw lu bi">', ''],
                                [' class="ln kb hi lj b fi lo lp l lq lr">', ''],
                                ['class="kn ko kp kq fd kr ks kt ku aw kv bi">', ''],
                                ['class="kw jl hi ks b fi kx ky l kz la">', ''],
                                ['class="example', ''],
                                ['class="python-exec">', ''],
                                ['class="python">', ''],
                                ['class="just-code notranslate language-python" data-lang="python3">', ''],
                                ['class="prettyprint">', ''],
                                ['class="prettyprint notranslate">', ''],
                                ['class="wp-block-syntaxhighlighter-code ', ''],
                                ['class="wp-block-code language-python">', ''],
                                ['class="wp-block-codemirror-blocks-code-block code-block">', ''],
                                ['class="wp-block-code>', ''],
                                ['class="wp-block-', ''],
                                ['class="language-python">', ''],
                                ['class="“language-python”">', ''],
                                ['class="language-clike', ''],
                                ['class="language-like', ''],
                                ['class="language', ''],
                                ['class="just-code', ''],
                                ['class="highlight python', ''],
                                ['class="EnlighterJSRAW', ''],
                                ['class="python codecolorer">', ''],
                                ['<pre class="highlight">', ''],
                                ['class="highlight">', ''],
                                ['class="answercell post-layout--right">', ''],
                                ['class="brush: python; title: ; notranslate" title>', ''],
                                ['class="brush: python" title="Python Code:">', ''],
                                ['style="overflow-wrap', ''],
                                ['class="lang: decode:true "', ''],
                                ['class="lang', ''],
                                ['textarea readonly="', ''],
                                ['<code>', ''],
                                ['class="kj ', ''],
                                [' class="ln ', ''],
                                ['<pre>', ''] ]

        comment_delimiters = [  ['class="article-summary abstract">', ''],
                                ['class=text>', ''],
                                ['class="examples-description">', ''],
                                ['class="entry-content" itemprop="text">', ''],
                                ['id="index_page_top_text_box">', ''],
                                ['class="postcell post-layout--right">', ''],
                                ['class="post_body scaleimages"', ''],
                                ['class="entry-content"', ''],
                                ['class="nv-content-wrap entry-content">', ''],
                                ['class="entry-content"', ''],                                
                                ['<title>', ''],
                                ['class=cart-heading>', ''],
                                ['<tr>', ''] ]
        
        line_delimiters = [ 'class="line"',
                            'class="line number',
                            '<code class="hljs language-python">',
                            'class="crayon-line',
                            '<code>',
                            '<br/>',
                            '<<span class="',
                            '<DsoftN>' ]
        
        comment_line_delimiters = [ '<p>',
                                    '<DsoftN>' ]
        
        # Look for site specific delimiters:
        html_text, container_delimiters, comment_delimiters, line_delimiters,comment_line_delimiters = self._find_delimiters(url, html_text, container_delimiters, comment_delimiters, line_delimiters, comment_line_delimiters)
        
        # Find end string for code
        for idx, delim in enumerate(container_delimiters):
            if delim[1] == "":
                if delim[0][0] == "<":
                    container_delimiters[idx][1] = "</" + delim[0][1:]
                else:
                    pos = html_text.find(delim[0])
                    if pos >= 0:
                        start_pos = html_text[:pos+1].rfind("<")
                        tag_string = html_text[start_pos:pos].strip()
                        if tag_string.find(" ") > 0:
                            tag_string = tag_string[:tag_string.find(" ")]
                        tag_string = "</" + tag_string[1:]
                    else:
                        tag_string = ""
                    container_delimiters[idx][1] = tag_string
        # Find end string for comments
        for idx, delim in enumerate(comment_delimiters):
            if delim[1] == "":
                if delim[0][0] == "<":
                    comment_delimiters[idx][1] = "</" + delim[0][1:]
                else:
                    pos = html_text.find(delim[0])
                    if pos >= 0:
                        start_pos = html_text[:pos+1].rfind("<")
                        tag_string = html_text[start_pos:pos].strip()
                        tag_string = "</" + tag_string[1:]
                    else:
                        tag_string = ""
                    comment_delimiters[idx][1] = tag_string

        comments = self._parse_html(html_text, comment_delimiters, comment_line_delimiters, comments=True)
        code_examples =  self._parse_html(html_text, container_delimiters, line_delimiters)
        result = []
        if len(comments) == len(code_examples):
            for idx, block in enumerate(code_examples):
                if idx < len(comments):
                    result.append(comments[idx])
                result.append(block)
        else:
            for comment in comments:
                result.append(comment)
            for block in code_examples:
                result.append(block)

        return result

    def _find_delimiters(self, url: str, html_text: str, container_d: list, comment_d: list, line_d: list, comment_line_d: list) -> list:
        """If there are specific delimiters for the requested site, then it returns a list containing only those delimiters,
        if nothing is found, it returns the original list.
        """
        if url.find("www.tutorialspoint.com") >= 0:
            container_d = [ ['class="just-code notranslate language-python" data-lang="python3">', ''],
                            ['class="prettyprint notranslate">', '']]
            comment_d = [['class="col-sm-12 col-md-8 col-xl-6 rounded-3 tutorial-content" id="mainContent">', ''], ['<tr>', '']]
            line_d = ["<DsoftN>"]
        elif url.find("www.geeksforgeeks.org") >= 0:
            container_d = [ ['class=code>', ''],
                            ['class="code"', '']]
            line_d = ['class="line number', 'class="line"']
        elif url.find("www.pythontutorial.net") >= 0:
            container_d = [['class="wp-block-code"', '']]
            comment_d = [['<h2>Summary</h2>', '']]
            line_d = ['<code class="hljs language-python">']
            comment_line_d = ["<li>"]
        elif url.find("stackoverflow.com") >= 0:
            container_d = [['class="answercell post-layout--right">', '']]
            line_d = ['<code>']
            comment_d = [['class="postcell post-layout--right">', '']]
            comment_line_d = ['<p>']
        elif url.find("python-forum.io") >= 0:
            container_d = [['class="brush: python" title="Python Code:">', '']]
            line_d = ['<DsoftN>']
            comment_d = [['class="post_body scaleimages"', '']]
            comment_line_d = ['<DsoftN>']
        elif url.find("www.pythonguis.com") >= 0:
            container_d = [['class="python">', '']]
            line_d = ['<DsoftN>']
            comment_d = [['<title>', '']]
            comment_line_d = ['<DsoftN>']
        elif url.find("clay-atlas.com") >= 0:
            container_d = [['textarea readonly=""', '']]
            line_d = ['<DsoftN>']
            comment_d = [['class="nv-content-wrap entry-content">', '']]
            comment_line_d = ['<p>']
        elif url.find("www.programcreek.com") >= 0:
            container_d = [['class="prettyprint">', '']]
            line_d = ['<DsoftN>']
            comment_d = [['id="index_page_top_text_box">', '']]
            comment_line_d = ['<DsoftN>']
        elif url.find("hotexamples.com") >= 0:
            container_d = [['class="example"', '']]
            line_d = ['<DsoftN>']
            comment_d = [['class="examples-description">', '']]
            comment_line_d = ['<DsoftN>']
        elif url.find("programtalk.com") >= 0:
            container_d = [['class="language-clike"', '']]
            line_d = ['<DsoftN>']
            comment_d = [['class="entry-content"', '']]
            comment_line_d = ['<DsoftN>']
        elif url.find("codesuche.com") >= 0:
            container_d = [ ['style="font-size:70%" class="language-python"', ''], 
                            ['style="font-size:', '']]
            line_d = ['<DsoftN>']
            comment_d = [['class="entry-content"', '']]
            comment_line_d = ['<DsoftN>']
        elif url.find("pdoc.qt.io") >= 0:
            comment_d = [['class="pre">', '']]
            comment_line_d = ['<DsoftN>']
        elif url.find("likegeeks.com") >= 0:
            container_d = [['class="lang:python decode:true"', '']]
            line_d = ['<DsoftN>']
            comment_d = [['class="entry-content">', '']]
            comment_line_d = ['<p>']
        elif url.find("data-flair.training") >= 0:
            comment_d = [['id="challenge-error-title">', '']]
            comment_line_d = ['<DsoftN>']
        elif url.find("pypi.org") >= 0:
            container_d = [['<code>', '']]
            line_d = ['<DsoftN>']
            comment_d = [['class="project-description">', '']]
            comment_line_d = ['<p>']
        elif url.find("www.guru99.com") >= 0:
            comment_d = [['<body>', '']]
            comment_line_d = ['<p>']
        elif url.find("docs.python.org") >= 0:
            container_d = [['class="highlight">', '']]
            line_d = ['<span class="gp">']
            comment_d = [['id="module', '']]
            comment_line_d = ['<p>']
        elif url.find("freecodecamp.org") >= 0:
            container_d = [['class="language-python">', '']]
            line_d = ['<DsoftN>']
            comment_d = [['class="post-content ">', '']]
            comment_line_d = ['<p>']
        elif url.find("realpython.com") >= 0:
            container_d = [ ['class="highlight python repl">', ''],
                            ['class="highlight python">', ''] ]
            line_d = ['<span class="gp">']
        elif url.find("www.programiz.com") >= 0:
            container_d = [['class="python-exec">', '']]
            line_d = ['<DsoftN>']
            comment_d = [['id="introduction">', '']]
            comment_line_d = ['<DsoftN>']
        elif url.find("www.w3schools.com") >= 0:
            container_d = [['class="w3-code notranslate pythonHigh">', '']]
            line_d = ['<br>']
            comment_d = [['<h1>', '']]
            comment_line_d = ['<DsoftN>']
        elif url.find("www.edureka.co") >= 0:
            container_d = [['class="brush: python; title: ; notranslate" title>', '']]
            line_d = ['<DsoftN>']
            comment_d = [['class=cart-heading>', '']]
            comment_line_d = ['<DsoftN>']
        elif url.find("pythonpyqt.com") >= 0:
            container_d = [['<code>', '']]
            line_d = ['<DsoftN>']
            comment_d = [['<h1>', '']]
            comment_line_d = ['<DsoftN>']
        elif url.find("coderslegacy.com") >= 0:
            container_d = [['class="wp-block-syntaxhighlighter', '']]
            line_d = ['<DsoftN>']
            comment_d = [['class="entry-content" itemprop="text">', '']]
            comment_line_d = ['<p>']
        elif url.find("www.machinelearningplus.com") >= 0:
            container_d = [['class="lang-python">', '']]
            line_d = ['<DsoftN>']
        elif url.find("www.pythonforbeginners.com") >= 0:
            container_d = [ ['class="language-python">', ''],
                            ['class="“language-python”">', '']]
            line_d = ['<DsoftN>']
            comment_d = [['class="entry-content">', '']]
            comment_line_d = ['<p>']
        elif url.find("sparkbyexamples.com") >= 0:
            container_d = [['class="language-python">', '']]
            line_d = ['<DsoftN>']
        elif url.find("datagy.io") >= 0:
            container_d = [ ['class="wp-block-code language-python">', ''],
                            ['class="wp-block-code', '']]
            line_d = ['<DsoftN>']
        elif url.find("www.knowprogram.com") >= 0:
            container_d = [['class="wp-block-code">', '']]
            line_d = ['<DsoftN>']
        elif url.find("blog.devgenius.io") >= 0:
            html_text = html_text.replace("<span id=", "<Dsoftn><br/><")
        elif url.find("github.com") >= 0:
            comment_d = [['data-target="readme-toc.content"', '']]
            comment_line_d = ['dir="auto"']
        elif url.find("www.techrepublic.com") >= 0:
            container_d = [['<pre>', '']]
            line_d = ['<DsoftN>']
            comment_d = [['class="article-summary abstract">', '']]
            comment_line_d = ['<DsoftN>']
        elif url.find("www.turing.com") >= 0:
            container_d = [['class="RichText_root__PJzIA ResourcesContent', '']]
            line_d = ['<p>']
        elif url.find("blog.gitnux.com") >= 0:
            container_d = [['<code>', '']]

        return html_text, container_d, comment_d, line_d, comment_line_d
    
    def _fix_html(self, url: str, html_text: str) -> str:
        """Fixes the HTML code depending on the site from which the data is downloaded.
        """
        if url.find("www.geeksforgeeks.org") >= 0:
            pos = 0
            while True:
                pos = html_text.find("<code class=keyword>", pos)
                if pos >= 0:
                    pos2 = html_text.find("<", pos+20)
                    if pos2 == -1:
                        break
                    html_text = html_text[:pos+1] + "<DsoftN>" + html_text[pos+20:pos2] + " " + html_text[pos2:]
                else:
                    break
        elif url.find("www.freecodecamp.org"):
            html_text = html_text.replace('<code class="language-python">', '\n<code class="language-python">')
        
        
        # Global rules
        html_text = html_text.replace('title">', "DsoftN> ")
        # html_text = html_text.replace('class="title">', "DsoftN> ")
        # html_text = html_text.replace('span class="hljs-title">', "DsoftN> ")

        return html_text


    def _parse_html(self, html: str, container_delimiters: list, line_delimiters: list, comments: bool = False) -> list:
        """Parsing HTML code, trying to find Code Examples.
        Args:
            html (str): HTML code
            container_delimiters (list): list of expresions that can be delimiters for code blocks
            line_delimiters (list): list of expresions that can be delimiters for code lines
            comments (bool): If true, search for comments
        Returns:
            list: [[code_title, code_body]]
        """
        code_list = []
        
        containers = []
        for container_delimiter in container_delimiters:
            containers = [x for x in html.split(container_delimiter[0]) if x != ""]
            if container_delimiter[0][-1:] != ">":
                containers = [("<" + x) for x in containers]
            if len(containers) > 1:
                for idx, container in enumerate(containers):
                    pos = container.find(container_delimiter[1])
                    if pos >=0:
                        containers[idx] = container[:pos]
                break
        if len(containers) <= 1:
            return []
        containers.pop(0)        
        
        code_block = []
        for idx_container, container in enumerate(containers):
            for line_delimiter in line_delimiters:
                code_block = [x + "<DsoftN>" for x in container.split(line_delimiter) if x != ""]
                if len(code_block) > 1:
                    if line_delimiter.find("DsoftN") >= 0:
                        code_block.pop(0)
                    break
            # if len(code_block) <= 1:
            #     continue
            code_body =  self._parse_code_block(code_block, line_delimiter)
            code_title = f"Example {str(idx_container+1)}/{len(containers)}"
            if comments:
                code_title = "|comment|"
            code_list.append([code_title, code_body])
        if code_list:
            return code_list
        else:
            return []

    def _parse_code_block(self, code_block: list, line_delimiter: str):
        """Parsing code block and trying to find code exapmples lines.
        Args:
            code_block (list): Code Block delimited with delimiter string
            line_delimiter = Used line delimiter
        """
        code_lines = []
        for line in code_block:
            if line_delimiter[-1] == ">":
                line = ">" + line
            code_line = ""
            idx = 0
            while idx <= len(line):
                char = line[idx:idx+1]

                if char == "<":
                    if line[idx:idx+2] == "< ":
                        code_line = code_line + "< "
                        idx += 1
                        char = ">"
                    else:
                        pos = line.find(">", idx)
                        if pos >= 0:
                            idx = pos-1
                        else:
                            break
                if char == ">":
                    pos = line.find("<", idx)
                    if pos < 0:
                        pos = len(line)
                    if line[idx+1:pos] != "":
                        code_line = code_line + line[idx+1:pos]
                    idx = pos-1
                idx += 1
            code_lines.append(code_line.replace("\xa0", " ") + "\n")
        
        code_body = "".join(code_lines)
        code_body = self._fix_ascii(code_body)

        return code_body

    def _fix_ascii(self, line: str) -> str:
        """Replaces special html characters with ASCII
        """
        html_entity = [ ["&nbsp;", " ", "non-breaking space"],
                        ["&#160;", " ", "non-breaking space"],
                        ["&#xa0;", " ", "non-breaking space"],
                        ["\\xa0", " ", "non-breaking space"],
                        ["&lt;", "<", "less than"],
                        ["&#x3c;", "<", "less than"],
                        ["\\x3c", "<", "less than"],
                        ["&gt;", ">", "greater than"],
                        ["&#x3e;", ">", "greater than"],
                        ["\\x3e", ">", "greater than"],
                        ["&amp;", "&", "ampersand"],
                        ["&#x26;", "&", "ampersand"],
                        ["\\x26", "&", "ampersand"],
                        ["&quot;", '"', "double quotation mark"],
                        ["&#x22;", '"', "double quotation mark"],
                        ["\\x22", '"', "double quotation mark"],
                        ["&apos;", "'", "single quotation mark (apostrophe)"],
                        ["&#x27;", "'", "single quotation mark (apostrophe)"],
                        ["\\x27", "'", "single quotation mark (apostrophe)"],
                        ["&cent;", "c", "cent"],
                        ["&#162;", "c", "cent"],
                        ["&pound;", "(POUND)", "pound"],
                        ["&#163;", "(POUND)", "pound"],
                        ["&yen", "(YEN)", "yen"],
                        ["&#165;", "(YEN)", "yen"],
                        ["&euro;", "(EURO)", "euro"],
                        ["&#8364;", "(EURO)", "euro"],
                        ["&copy;", "(c)", "copyright"],
                        ["&#169;", "(c)", "copyright"],
                        ["&reg;", "(r)", "registered trademark"],
                        ["&#174;", "(r)", "registered trademark"],
                        ["&iexcl;", "(!)", "INVERTED EXCLAMATION MARK"],
                        ["&#161;", "(!)", "INVERTED EXCLAMATION MARK"],
                        ["&sect;", "(S)", "SECTION SIGN"],
                        ["&#167;", "(S)", "SECTION SIGN"],
                        ["&laquo;", "<<", "DOUBLE LEFT-POINTING ANGLE QUOTATION MARK"],
                        ["&#171;", "<<", "DOUBLE LEFT-POINTING ANGLE QUOTATION MARK"],
                        ["&raquo;", ">>", "DOUBLE RIGHT-POINTING ANGLE QUOTATION MARK"],
                        ["&#187;", ">>", "DOUBLE RIGHT-POINTING ANGLE QUOTATION MARK"],
                        ["&sup1;", "(1)", "SUPERSCRIPT ONE"],
                        ["&#185;", "(1)", "SUPERSCRIPT ONE"],
                        ["&sup2;", "(2)", "SUPERSCRIPT TWO"],
                        ["&#178;", "(2)", "SUPERSCRIPT TWO"],
                        ["&sup3;", "(3)", "SUPERSCRIPT THREE"],
                        ["&#179;", "(3)", "SUPERSCRIPT THREE"],
                        ["&para;", "--(P)", "PARAGRAPH SIGN"],
                        ["&#182;", "--(P)", "PARAGRAPH SIGN"],
                        ["&iquest;", "(?)", "INVERTED QUESTION MARK"],
                        ["&#191;", "(?)", "INVERTED QUESTION MARK"],
                        ["&hyphen;", "-", "HYPHEN"],
                        ["&#8208;", "-", "HYPHEN"],
                        ["&#8209;", "-", "NON-BREAKING HYPHEN"],
                        ["&Vert;", "||", "DOUBLE VERTICAL LINE"],
                        ["&#8214;", "||", "DOUBLE VERTICAL LINE"],
                        ["&bull;", "*", "BULLET"],
                        ["&#8226;", "*", "BULLET"],
                        ["&#8227;", ">", "TRIANGULAR BULLET"],
                        ["&tprime;", '"""', "TRIPLE PRIME"],
                        ["&#8244;", '"""', "TRIPLE PRIME"],
                        ["&#8264;", "?!", "QUESTION EXCLAMATION MARK"],
                        ["&#8265;", "!?", "EXCLAMATION QUESTION MARK"],
                        ["&trade;", "(tm)", "TRADE MARK SIGN"],
                        ["&#8482;", "(tm)", "TRADE MARK SIGN"],
                        ["&#8451;", "^C", "DEGREE CELSIUS"],
                        ["&#8457;", "^F", "DEGREE FAHRENHEIT"],
                        ["&female;", "(F)", "FEMALE SIGN"],
                        ["&#9792;", "(F)", "FEMALE SIGN"],
                        ["&male;", "(M)", "MALE SIGN"],
                        ["&#9794;", "(M)", "MALE SIGN"],
                        ["&check;", "(Ok)", "CHECK MARK"],
                        ["&#10003;", "(Ok)", "CHECK MARK"],
                        ["&crarr;", "(RETURN)", "DOWN ARROW WITH CORNER LEFT"],
                        ["&#8629;", "(RETURN)", "DOWN ARROW WITH CORNER LEFT"],
                        ["&#10529;", "(RESIZE)", "NORTH WEST AND SOUTH EAST ARROW"],
                        ["&#10530;", "(RESIZE)", "NORTH EAST AND SOUTH WEST ARROW"],
                        ["&ETH;", "DJ", "UPPERCASE ETH"],
                        ["&#208;", "DJ", "UPPERCASE ETH"],
                        ["&Euml;", "E", "UPPERCASE E WITH UMLAUT"],
                        ["&#203;", "E", "UPPERCASE E WITH UMLAUT"],
                        ["&Ouml;", "O", "UPPERCASE O WITH UMLAUT"],
                        ["&#214;", "O", "UPPERCASE O WITH UMLAUT"],
                        ["&Uuml;", "U", "UPPERCASE U WITH UMLAUT"],
                        ["&#220;", "U", "UPPERCASE U WITH UMLAUT"],
                        ["&auml;", "a", "LOWERCASE A WITH UMLAUT"],
                        ["&#228;", "a", "LOWERCASE A WITH UMLAUT"],
                        ["&euml;", "e", "LOWERCASE E WITH UMLAUT"],
                        ["&#235;", "e", "LOWERCASE E WITH UMLAUT"],
                        ["&iuml;", "i", "LOWERCASE I WITH UMLAUT"],
                        ["&#239;", "i", "LOWERCASE I WITH UMLAUT"],
                        ["&ouml;", "o", "LOWERCASE O WITH UMLAUT"],
                        ["&#246;", "o", "LOWERCASE O WITH UMLAUT"],
                        ["&uuml;", "u", "LOWERCASE U WITH UMLAUT"],
                        ["&#252;", "u", "LOWERCASE U WITH UMLAUT"],
                        ["&Cacute;", "C", "UPPERCASE C WITH ACUTE"],
                        ["&#262;", "C", "UPPERCASE C WITH ACUTE"],
                        ["&cacute;", "c", "LOWERCASE C WITH ACUTE"],
                        ["&#263;", "c", "LOWERCASE C WITH ACUTE"],
                        ["&Ccaron;", "C", "UPPERCASE C WITH CARON"],
                        ["&#268;", "C", "UPPERCASE C WITH CARON"],
                        ["&ccaron;", "c", "LOWERCASE C WITH CARON"],
                        ["&#269;", "c", "LOWERCASE C WITH CARON"],
                        ["&Dstrok;", "DJ", "UPPERCASE D WITH STROKE"],
                        ["&#272;", "DJ", "UPPERCASE D WITH STROKE"],
                        ["&dstrok;", "dj", "LOWERCASE D WITH STROKE"],
                        ["&#273;", "dj", "LOWERCASE D WITH STROKE"],
                        ["&Scaron;  ", "S", "UPPERCASE S WITH CARON"],
                        ["&#352;", "S", "UPPERCASE S WITH CARON"],
                        ["&scaron;", "s", "LOWERCASE S WITH CARON"],
                        ["&#353;", "s", "LOWERCASE S WITH CARON"],
                        ["&Zcaron;", "Z", "UPPERCASE Z WITH CARON"],
                        ["&#381;", "Z", "UPPERCASE Z WITH CARON"],
                        ["&zcaron;", "z", "LOWERCASE Z WITH CARON"],
                        ["&#382;", "z", "LOWERCASE Z WITH CARON"],
                        ["&#393;", "DJ", "UPPERCASE AFRICAN D"],
                        ["&#452;", "DZ", "UPPERCASE DZ WITH CARON"],
                        ["&#453;", "Dz", "UPPERCASE D WITH SMALL LETTER Z WITH CARON"],
                        ["&#454;", "dz", "LOWERCASE DZ WITH CARON"],
                        ["&#455;", "LJ", "UPPERCASE LJ"],
                        ["&#456;", "Lj", "UPPERCASE L WITH SMALL LETTER J"],
                        ["&#457;", "lj", "LOWERCASE LJ"],
                        ["&#458;", "NJ", "UPPERCASE NJ"],
                        ["&#459;", "Nj", "UPPERCASE N WITH SMALL LETTER J"],
                        ["&#460;", "nj", "LOWERCASE NJ"],
                        ["&divide;", "/", "DIVISION SIGN"],
                        ["&#247;", "/", "DIVISION SIGN"],
                        ["&ne;", "<>", "NOT EQUAL TO SIGN"],
                        ["&#8800;", "<>", "NOT EQUAL TO SIGN"],
                        ["&deg;", "^", "DEGREE SIGN"],
                        ["&#176;", "^", "DEGREE SIGN"],
                        ["&fnof;", "(Func)", "FUNCTION"],
                        ["&#402;", "(Func", "FUNCTION"],
                        ["&empty;", "0", "EMPTY SET"],
                        ["&#8709;", "0", "EMPTY SET"],
                        ["&radic;", "(Sqr)", "SQUARE ROOT"],
                        ["&#8730;", "(Sqr)", "SQUARE ROOT"],
                        ["&mid;", "|", "DIVIDES"],
                        ["&#8739;", "|", "DIVIDES"],
                        ["&sim;", "~", "TILDE OPERATOR"],
                        ["&#8764;", "~", "TILDE OPERATOR"],
                        ["&#8797;", "(=DEF)", "EQUAL TO BY DEFINITION"],
                        ["&frac12;", "1/2", "FRACTION ONE HALF"],
                        ["&#189;", "1/2", "FRACTION ONE HALF"],
                        ["&frac14;", "1/4", "FRACTION ONE QUARTER"],
                        ["&#188;", "1/4", "FRACTION ONE QUARTER"],
                        ["&frac13;", "1/3", "VULGAR FRACTION ONE THIRD"],
                        ["&#8531;", "1/3", "VULGAR FRACTION ONE THIRD"],
                        ["&minus;", "-", "minus"],
                        ["&#8722;", "-", "minus"],
                        ["&plusmn;", "+/-", "PLUS OR MINUS SIGN"],
                        ["&#177;", "+/-", "PLUS OR MINUS SIGN"] ]

        if line.find("&") >=0:
            for entity in html_entity:
                line = line.replace(entity[0], entity[1])
        if line.find("&") >=0:
            for entity in html_entity:
                line = line.replace(entity[0], entity[1])

        pos=0
        while pos >= 0:
            pos = line.find("&#")
            if pos >= 0:
                end_pos = line[pos:].find(";") + pos
                ascii_string = line[pos:end_pos]
                if ascii_string[2:].isdigit():
                    ascii_val = int(ascii_string[2:])
                else:
                    ascii_val = 0
                lenght = len(ascii_string) + 1
                replace_char = ""
                if ascii_val > 31 and ascii_val < 127:
                    replace_char = chr(ascii_val)
                line = line[:pos] + replace_char + line[pos+lenght:]

        # Fix other
        if line.find("Code language:") > 0:
            line = line[:line.find("Code language:")]

        return line

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
    # Samo za testiranje OBRISI
    # url = "https://pythonprogramminglanguage.com/pyqt-line-edit/"
    # url = "https://www.geeksforgeeks.org/pyqt5-qlineedit/"
    url = "https://www.knowprogram.com/python/reverse-number-python/"
    tmp.get_code_examples_all(url)

    # OBRISI sve gore
