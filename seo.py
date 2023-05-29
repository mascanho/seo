from urllib.parse import urljoin, urlparse

import nltk
import requests
from bs4 import BeautifulSoup
from bs4.element import Comment
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.tokenize import word_tokenize


# ANSI escape codes for color formatting
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[31m"
    ENDC = "\033[0m"


def get_page_title(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.string.strip() if soup.title else "No title found"
    return title


def get_page_description(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    meta_tags = soup.find_all("meta")
    description = ""
    for tag in meta_tags:
        if "name" in tag.attrs and tag.attrs["name"].lower() == "description":
            description = tag.attrs["content"].strip()
            break
    return description if description else "No description found"


def get_page_keywords(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text()

    # Download the 'punkt' and 'stopwords' resources if not already downloaded
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt")

    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("stopwords")

    tokens = word_tokenize(text)
    # Filter out stopwords and non-alphabetic tokens
    stopwords_list = set(stopwords.words("english"))
    keywords = [
        token.lower()
        for token in tokens
        if token.isalpha() and token.lower() not in stopwords_list
    ]
    freq_dist = FreqDist(keywords)
    top_keywords = freq_dist.most_common(10)  # Get the 10 most common keywords
    return top_keywords


def get_response_code(url):
    response = requests.get(url)
    return response.status_code


def get_url_chain(url):
    response = requests.get(url)
    chain = [url]
    redirects = response.history
    for redirect in redirects:
        chain.append(redirect.url)
    return chain


def get_heading_structure(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    heading_structure = {}
    for heading in headings:
        level = int(heading.name[1])
        text = heading.get_text().strip()
        if level in heading_structure:
            heading_structure[level].append(text)
        else:
            heading_structure[level] = [text]
    return heading_structure


def get_hreflang_tags(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    hreflang_tags = soup.find_all("link", rel="alternate", hreflang=True)
    hreflang_urls = []
    for tag in hreflang_tags:
        hreflang_url = tag.get("href", "")
        if hreflang_url:
            hreflang_urls.append(hreflang_url)
    return hreflang_urls


def tag_visible(element):
    if element.parent.name in [
        "style",
        "script",
        "head",
        "title",
        "meta",
        "[document]",
        "footer",
    ]:
        return False
    if isinstance(element, Comment):
        return False
    return True


# Function to check if a tag should be excluded
def should_exclude_tag(tag):
    excluded_tags = ["footer", "header"]  # List of tags to exclude
    return tag.name in excluded_tags


# Function to check if an element should be excluded based on classnames or ids
def should_exclude_element(element):
    excluded_classnames = [
        "header-wrapper",
        "header-menu-mobile",
        "footer",
        "footer-left",
        "footer-top",
        "footer-block",
        "footer-blocks",
        "footer-bottom",
        "right",
        "left",
        "date",
        "related-items",
    ]  # List of classnames to exclude
    excluded_ids = ["exclude-id1", "exclude-id2"]  # List of ids to exclude
    return (
        element.get("class")
        and any(classname in excluded_classnames for classname in element["class"])
        or element.get("id")
        and element["id"] in excluded_ids
    )


# Function to get all links from a webpage, excluding certain classnames, ids, tags, internal links with "#" and considering same domain
def get_all_links(url):
    # Send a GET request to the specified URL
    response = requests.get(url)

    # Create a BeautifulSoup object from the response content
    soup = BeautifulSoup(response.content, "html.parser")

    # List to store all links and their anchor texts
    all_links = []

    # Get the base URL to resolve relative URLs
    base_url = response.url

    # Get the domain of the base URL
    base_domain = urlparse(base_url).netloc

    # Recursively traverse the DOM tree within the <body> element
    def traverse(element):
        if element.name == "a":
            # Exclude tags
            if should_exclude_tag(element):
                return

            # Exclude elements based on classnames or ids
            parent_element = element.parent
            while parent_element and not parent_element.name == "body":
                if should_exclude_element(parent_element):
                    return
                parent_element = parent_element.parent

            href = element.get("href")
            anchor_text = element.get_text().strip()

            # Check if the href attribute exists, the link matches the same domain, and it's not an internal link with "#"
            if href:
                # Resolve relative URLs
                absolute_url = urljoin(base_url, href)
                parsed_url = urlparse(absolute_url)
                link_domain = parsed_url.netloc

                # Consider only links with the same domain and exclude internal links with "#"
                if link_domain == base_domain and not href.startswith("#"):
                    all_links.append((absolute_url, anchor_text))

        for child in element.children:
            if child.name and not isinstance(child, str):
                traverse(child)

    # Find the <body> element
    body = soup.find("body")

    # Traverse the DOM tree starting from the <body> element
    if body:
        traverse(body)

    return all_links


# Prompt the user to input the URL
url = input("Enter the URL: ")

# Get the page title, description, keywords, response code, URL chain, heading structure,
# hreflang tags, and internal links
title = get_page_title(url)
description = get_page_description(url)
keywords = get_page_keywords(url)
response_code = get_response_code(url)
url_chain = get_url_chain(url)
heading_structure = get_heading_structure(url)
hreflang_urls = get_hreflang_tags(url)
internal_links = get_all_links(url)

# Output the results with color formatting
print("\n")
print(f"{Colors.RED}Analysing: {Colors.ENDC}{Colors.BLUE}{url}{Colors.ENDC}")
print("\n")
print(f"{Colors.HEADER}Page title: {Colors.BLUE}{title}{Colors.ENDC}\n")
print(f"{Colors.HEADER}Page description: {Colors.BLUE}{description}{Colors.ENDC}\n")
print(f"{Colors.HEADER}Page keywords:{Colors.ENDC}\n")
for keyword, frequency in keywords:
    print(f"- {Colors.YELLOW}{keyword}{Colors.ENDC}: {frequency}")
print("\n")
print(f"{Colors.HEADER}Response code: {Colors.BLUE}{response_code}{Colors.ENDC}\n")
print(f"{Colors.HEADER}URL Chain:{Colors.ENDC}\n")
for chain_url in url_chain:
    parsed_url = urlparse(chain_url)
    print(f"- {Colors.GREEN}{parsed_url.netloc}{Colors.ENDC}{parsed_url.path}")
print("\n")
print(f"{Colors.HEADER}Heading Structure:{Colors.ENDC}\n")
for level, headings in heading_structure.items():
    for heading in headings:
        heading_tag = f"{Colors.YELLOW}h{level}{Colors.ENDC}"
        print(f"{heading_tag}: {Colors.BLUE}{heading}{Colors.ENDC}")

print(f"\n{Colors.HEADER}Hreflang URLs:\n")
for hreflang_url in hreflang_urls:
    print(f"{Colors.BLUE}{hreflang_url}{Colors.ENDC}")

print(f"\n{Colors.HEADER}Internal Links (excluding footer and navbar):\n")
for internal_link, anchor_text in internal_links:
    print(
        f"{Colors.YELLOW}{anchor_text}{Colors.ENDC}: {Colors.BLUE}{internal_link}{Colors.ENDC}"
    )
