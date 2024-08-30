import argparse
import requests
from bs4 import BeautifulSoup
import time
import ssl
import re
from urllib.parse import urlparse
from requests.exceptions import SSLError

from langdetect import detect
from nltk.corpus import stopwords

# ANSI escape sequences for colors and symbols
COLOR_GREEN = '\033[92m'  # Green
COLOR_YELLOW = '\033[93m'  # Yellow
COLOR_RED = '\033[91m'     # Red
COLOR_BLUE = '\033[94m'    # Light Blue
COLOR_PURPLE = '\033[95m'  # Purple
COLOR_LIGHT_GRAY = '\033[37m'  # Light Gray
COLOR_LIGHT_BLUE = '\033[96m'  # Light Blue
COLOR_RESET = '\033[0m'    # Reset
SYMBOL_GOOD = '●'          # Green dot
SYMBOL_NEUTRAL = '●'       # Yellow dot
SYMBOL_FAIL = '■'          # Exclamation mark

# SEO character count limits
SEO_TITLE_LIMITS = (50, 60)  # Optimal: 50-60 characters
SEO_DESC_LIMITS = (150, 160)  # Optimal: 150-160 characters
SEO_H1_LIMIT = 70  # Optimal: up to 70 characters

LANGUAGE_MAP = {
    'de': 'german',
    'el': 'greek',
    'en': 'english',
    'es': 'spanish',
    'fi': 'finnish',
    'fr': 'french',
    'it': 'italian',
    'nl': 'dutch',
    'no': 'norwegian',
    'pl': 'polish',  # Not available in NLTK stopwords
    'pt': 'portuguese',
    'sv': 'swedish',
    'zh': 'chinese'
}


def color_print(status, label, content):
    """
    Prints colored output based on the status, label, and content.

    Parameters:
    status (str): Status of the information ('GOOD', 'NEUTRAL', 'FAIL', 'SECTION')
    label (str): Label of the information
    content (str): Content of the information
    """
    if status == 'GOOD':
        symbol = f"{COLOR_GREEN}{SYMBOL_GOOD}{COLOR_RESET}"
    elif status == 'NEUTRAL':
        symbol = f"{COLOR_LIGHT_GRAY}{SYMBOL_NEUTRAL}{COLOR_RESET}"
    elif status == 'FAIL':
        symbol = f"{COLOR_RED}{SYMBOL_FAIL}{COLOR_RESET}"
    elif status == 'SECTION':
        symbol = f"{COLOR_BLUE}>{COLOR_RESET}"
    else:
        symbol = ''  # Default without symbol

    print(f"{symbol} {COLOR_LIGHT_BLUE}{label}{':' if content else ''}{COLOR_RESET} {content}")

def print_separator():
    """ Prints a separator for output. """
    print(f"{COLOR_RESET}{'-' * 50}{COLOR_RESET}")
    
def section_header(title):
    """ Prints a separator for output. """
    print()
    print(f"{COLOR_BLUE}>>> {title} >>>{COLOR_RESET}")


def fetch_url_content(url, follow_redirects):
    """
    Fetches the content of the given URL and follows redirects if specified.

    Parameters:
    url (str): The URL to be fetched.
    follow_redirects (bool): Indicates whether to follow redirects.

    Returns:
    response (requests.Response): The response object containing the URL content.
    """
    section_header('Performance')
    try:
        start_time = time.time()
        response = requests.get(url, allow_redirects=follow_redirects)
        response.raise_for_status()  # Check for HTTP errors
        total_time = time.time() - start_time
        color_print('GOOD', 'Initial response time',
                    f"{response.elapsed.total_seconds()} seconds")
        color_print('GOOD', 'Total load time', f"{total_time:.2f} seconds")
        color_print('GOOD', 'Page size',
                    f"{len(response.content) / 1024:.2f} KB")
        return response
    except requests.exceptions.RequestException as e:
        color_print('FAIL', 'Error', f"Failed to fetch URL: {e}")
        return None


def print_redirect_history(response):
    """
    Prints the full redirect history of the response.

    Parameters:
    response (requests.Response): The response object containing the URL content.
    """
    section_header('Redirects')
    if response.history:
        for i, resp in enumerate(response.history):
            color_print(
                'NEUTRAL', f"Step {i + 1}", f"{resp.url} (Status Code: {resp.status_code})")
        color_print('GOOD', 'Final URL',
                    f"{response.url} (Status Code: {response.status_code})")
    else:
        color_print('NEUTRAL', 'Redirect history', 'No redirects found.')


def print_status_code(response):
    """
    Prints the status code of the response.

    Parameters:
    response (requests.Response): The response object containing the URL content.
    """
    section_header('Status Code')
    status = 'GOOD' if response.status_code == 200 else 'FAIL'
    color_print(status, 'Status Code', response.status_code)


def semantic_analysis(response):
    """
    Performs a semantic analysis of all text on the page and finds relevant keywords.

    Parameters:
    response (requests.Response): The response object containing the URL content.
    """
    section_header('Semantic Analysis')

    soup = BeautifulSoup(response.text, 'html.parser')
    texts = soup.stripped_strings
    text_content = ' '.join(texts)

    # Detect the language of the document
    try:
        detected_language = detect(text_content)
        color_print('GOOD', 'Document Language', detected_language)
    except Exception as e:
        color_print('FAIL', 'Language Detection',
                    f"Error detecting language: {e}")
        return

    # Map detected language to NLTK stopwords
    nltk_language = LANGUAGE_MAP.get(detected_language)
    if not nltk_language:
        color_print('FAIL', 'Stopwords',
                    f"Stopwords not available for detected language '{detected_language}'")
        return

    # Get the list of stopwords for the detected language
    try:
        stop_words = set(stopwords.words(nltk_language))
    except Exception as e:
        color_print('FAIL', 'Stopwords',
                    f"Error retrieving stopwords for language '{nltk_language}': {e}")
        return

    # Normalize text: lowercase and remove extra whitespace
    words = re.findall(r'\b\w+\b', text_content.lower())

    # Filter text content to exclude stopwords
    filtered_words = [word for word in words if word not in stop_words]

    # Calculate word frequency
    word_frequency = {}
    for word in filtered_words:
        word_frequency[word] = word_frequency.get(word, 0) + 1

    # Output relevant keywords
    keywords = sorted(word_frequency.items(),
                      key=lambda item: item[1], reverse=True)[:10]
    color_print('GOOD', 'Relevant Keywords',
                ', '.join([kw[0] for kw in keywords]))


def print_links_info(response):
    """
    Analyzes internal and external links and outputs them.

    Parameters:
    response (requests.Response): The response object containing the URL content.
    """
    section_header('Link Analysis')
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', href=True)
    internal_links = []
    external_links = []
    base_url = urlparse(response.url).netloc

    for link in links:
        href = link['href']
        # Ignore links with 'tel' and 'mailto' prefixes
        if href.startswith('tel:') or href.startswith('mailto:') or href.startswith('javascript:'):
            continue

        full_url = requests.compat.urljoin(response.url, href)
        link_base_url = urlparse(full_url).netloc

        # Determine if the link is internal or external
        if link_base_url == base_url:
            internal_links.append(full_url)
        else:
            external_links.append(full_url)

    # Output internal links
    color_print('SECTION', 'Internal links', '')
    for url in internal_links:
        try:
            link_response = requests.get(url)
            if 200 <= link_response.status_code < 300:
                status = 'GOOD'
            elif 300 <= link_response.status_code < 400:
                status = 'NEUTRAL'
            else:
                status = 'FAIL'
            color_print(status, 'Link',
                        f"Status: {link_response.status_code}, URL: {url}")
        except requests.RequestException as e:
            color_print('FAIL', 'Link', f"Error fetching URL: {url} - {e}")

    # Output external links
    color_print('SECTION', 'External links', '')
    for url in external_links:
        try:
            link_response = requests.get(url)
            if 200 <= link_response.status_code < 300:
                status = 'GOOD'
            elif 300 <= link_response.status_code < 400:
                status = 'NEUTRAL'
            else:
                status = 'FAIL'
            color_print(status, 'Link',
                        f"Status: {link_response.status_code}, URL: {url}")
        except requests.RequestException as e:
            color_print('FAIL', 'Link', f"Error fetching URL: {url} - {e}")



def evaluate_field_length(content, optimal_range):
    """
    Evaluates the length of a content field against an optimal character range.

    Parameters:
    content (str): The content to evaluate.
    optimal_range (tuple): A tuple with (min, max) optimal character length.

    Returns:
    status (str): Evaluation of the content ('GOOD', 'NEUTRAL', 'FAIL')
    """
    if not content:
        return 'FAIL'
    length = len(content)
    if optimal_range[0] <= length <= optimal_range[1]:
        return 'GOOD'
    return 'NEUTRAL'


def print_seo_relevant_header_info(response):
    """
    Outputs all SEO-relevant fields in the <header> of the webpage.

    Parameters:
    response (requests.Response): The response object containing the URL content.
    """
    
    section_header('SEO Header Analysis')

    soup = BeautifulSoup(response.text, 'html.parser')
    header = soup.find('head')

    if header:
        # Title output
        title = header.find('title')
        title_content = title.get_text(strip=True) if title else ''
        status = evaluate_field_length(title_content, SEO_TITLE_LIMITS)
        color_print(status, 'Title', title_content)

        # Meta description and keywords output
        meta_description = header.find('meta', attrs={'name': 'description'})
        desc_content = meta_description['content'] if meta_description and meta_description.get(
            'content') else ''
        status = evaluate_field_length(desc_content, SEO_DESC_LIMITS)
        color_print(status, 'Description', desc_content)

        # Canonical link output
        canonical_link = header.find('link', attrs={'rel': 'canonical'})
        canonical_content = canonical_link['href'] if canonical_link and canonical_link.get(
            'href') else ''
        if canonical_content:
            color_print('GOOD', 'Canonical', canonical_content)

    else:
        color_print('FAIL', 'Header', 'No <head> section found.')


def print_heading_tags(response):
    """
    Outputs all H1, H2, and H3 tags on the page.

    Parameters:
    response (requests.Response): The response object containing the URL content.
    """
    section_header('SEO Content Analysis')
    soup = BeautifulSoup(response.text, 'html.parser')
    if not any(soup.find_all(['h1'])):
        color_print('FAIL', 'Headings', 'No H1 tag found.')
    for heading in ['h1', 'h2', 'h3']:
        tags = soup.find_all(heading)
        for tag in tags:
            content = tag.get_text(strip=True)
            if heading == 'h1':
                status = evaluate_field_length(content, (1, SEO_H1_LIMIT))
            else:
                status = 'GOOD' if content else 'FAIL'
            color_print(status, heading.upper(), content)
    if len(soup.find_all(['h1'])) > 1:
        color_print('FAIL', 'Headings', 'Multiple H1 tags found.')

def print_media_info(response):
    """
    Outputs information about video, audio, and image content.

    Parameters:
    response (requests.Response): The response object containing the URL content.
    """
    section_header('SEO Media Analysis')
    soup = BeautifulSoup(response.text, 'html.parser')
    base_url = response.url  # Base URL for resolving relative URLs

    # Check for videos/audios
    videos = soup.find_all(['video', 'audio'])
    for media in videos:
        src = media.get('src', '')
        label = 'Video' if media.name == 'video' else 'Diverse (%s)' % media.name
        if src:
            color_print('GOOD', f'{label} Source', src)
        else:
            color_print('FAIL', f'{label}', 'No source found')

    # Check for images
    images = soup.find_all(['img', 'e-img'])
    for img in images:
        alt_text = img.get('alt', '')
        alt_text = alt_text if len(alt_text) < 50 else alt_text[:50] + '...'
        src = img.get('src', '')
        if src.startswith('data:'):
            color_print('NEUTRAL', 'Image',
                        'Inline image detected, no further analysis')
            continue
        img_name = src.split('/')[-1] if '/' in src else src
        img_name = img_name.split('?')[0]  # Remove query parameters
        img_name = img_name.split('#')[0]  # Remove fragments
        img_name = img_name if len(img_name) < 50 else img_name[:50] + '...'
        absolute_url = requests.compat.urljoin(
            base_url, src)  # Resolve relative URLs

        # Fetch image details
        try:
            img_response = requests.get(absolute_url, stream=True)
            img_size_kb = len(img_response.content) / 1024
            img_format = img_response.headers.get('Content-Type', 'Unknown')
            image_info = f"Filename: {img_name}, ALT: {alt_text or 'NOT PROVIDED'}, Size: {img_size_kb:.2f} KB, Format: {img_format}"
            color_print('GOOD' if alt_text else 'FAIL', 'Image', image_info)
        except requests.RequestException as e:
            color_print('FAIL', 'Image',
                        f"{img_name}, Error fetching image: {e}")



def check_google_index_status(url):
    """
    Checks if the URL is indexed by Google.

    Parameters:
    url (str): The URL to check.

    Note:
    This function performs a search query using Google's 'site:' operator.
    """
    section_header('Google Index Status')
    try:
        search_url = f"https://www.google.com/search?q=site:{url}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(search_url, headers=headers)
        if response.status_code == 200:
            if 'did not match any documents' in response.text:
                color_print('FAIL', 'Google Index',
                            'URL not found in Google index')
            else:
                color_print('GOOD', 'Google Index', 'URL is indexed by Google')
        else:
            color_print('FAIL', 'Google Index',
                        f"Failed to check Google index (Status Code: {response.status_code})")
    except requests.RequestException as e:
        color_print('FAIL', 'Google Index',
                    f"Error while checking Google index: {e}")
        


def check_server_info(url):
    """
    Checks server information, including sitemap, robots.txt, SSL certificate, IP address, and server software.

    Parameters:
    url (str): The URL to check.
    """
    section_header('Server Information')

    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    # Check for sitemap
    sitemap_url = f"{base_url}/sitemap.xml"
    try:
        sitemap_response = requests.get(sitemap_url)
        if sitemap_response.status_code == 200:
            color_print('GOOD', 'Sitemap', f"Found at {sitemap_url}")
        else:
            color_print('FAIL', 'Sitemap', 'Not found')
    except requests.RequestException:
        color_print('FAIL', 'Sitemap', 'Error checking sitemap')

    # Check for robots.txt
    robots_url = f"{base_url}/robots.txt"
    try:
        robots_response = requests.get(robots_url)
        if robots_response.status_code == 200:
            color_print('GOOD', 'robots.txt', f"Found at {robots_url}")
        else:
            color_print('FAIL', 'robots.txt', 'Not found')
    except requests.RequestException:
        color_print('FAIL', 'robots.txt', 'Error checking robots.txt')

    # Check SSL certificate
    try:
        requests.get(url, verify=True)  # Perform request to check SSL validity
        color_print('GOOD', 'SSL Certificate', 'Valid')
    except requests.exceptions.SSLError:
        color_print('FAIL', 'SSL Certificate', 'Invalid or not present')

    # Get server IP and software
    try:
        ip_address = requests.get(
            f"https://dns.google/resolve?name={parsed_url.netloc}").json()
        if 'Answer' in ip_address:
            server_ip = ip_address['Answer'][0]['data']
            color_print('GOOD', 'Server IP', server_ip)
        else:
            color_print('FAIL', 'Server IP', 'Could not retrieve IP address')
    except requests.RequestException:
        color_print('FAIL', 'Server IP', 'Error retrieving IP address')

    # Check server software
    try:
        server_response = requests.head(url)
        server_software = server_response.headers.get('Server', 'Unknown')
        color_print('NEUTRAL', 'Server Software', server_software)
    except requests.RequestException:
        color_print('FAIL', 'Server Software',
                    'Error retrieving server software information')
        

def main():
    # Initialize argument parser
    parser = argparse.ArgumentParser(
        description="Retrieve SEO-relevant data for a specific URL")

    # Add URL parameter
    parser.add_argument('--url', type=str, required=True,
                        help='The URL to retrieve SEO-relevant data for')

    # Add follow redirects parameter
    parser.add_argument('-f', '--follow', action='store_true',
                        help='Follow redirects until there are no more')

    # Add media analysis parameter
    parser.add_argument('-m', '--media', action='store_true',
                        help='Analyze media content (video, audio, images) on the page')

    # Add link analysis parameter with short version
    parser.add_argument('-l', '--links', action='store_true',
                        help='Output all internal and external links on the page')

    # Add server check parameter with short version
    parser.add_argument('-s', '--server', action='store_true',
                        help='Check for sitemap, robots.txt, SSL certificate status, and server info')

    # Add Google index check parameter with short version
    parser.add_argument('-g', '--google', action='store_true',
                        help='Check if the URL is indexed by Google')

    # Add content analysis parameter with short version
    parser.add_argument('-c', '--content', action='store_true',
                        help='Output heading tags (H1, H2, H3) from the page')

    # Add semantic analysis parameter with short version
    parser.add_argument('-e', '--semantic', action='store_true',
                        help='Perform semantic analysis on the page content')

    # Add all-inclusive parameter
    parser.add_argument('-a', '--all', action='store_true',
                        help='Run all checks and outputs (equivalent to setting all parameters)')

    # Parse arguments
    args = parser.parse_args()

    # Extract URL and options from arguments
    url = args.url
    follow_redirects = args.follow or args.all
    analyze_media = args.media or args.all
    check_links = args.links or args.all
    check_server = args.server or args.all
    google_check = args.google or args.all
    check_content = args.content or args.all
    perform_semantic = args.semantic or args.all

    if check_server:
        check_server_info(url)  # Check server information

    # Fetch URL content
    response = fetch_url_content(url, follow_redirects)

    if response:
        print_redirect_history(response)  # Output redirect history
        print_status_code(response)  # Output status code
        if google_check:
            check_google_index_status(url)  # Check if URL is indexed by Google
        # Output SEO-relevant fields in <header>
        print_seo_relevant_header_info(response)
        if check_content:
            # Output all H1, H2, and H3 tags if content parameter is set
            print_heading_tags(response)
        if perform_semantic:
            semantic_analysis(response)  # Perform semantic analysis
        if analyze_media:
            print_media_info(response)  # Output media content information
        if check_links:
            print_links_info(response)  # Output internal and external links
    else:
        color_print('FAIL', 'Fetch', 'Failed to retrieve the URL.')


if __name__ == "__main__":
    main()
