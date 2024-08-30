
# SEO Analysis Tool

This is a badly written but useful Python-based SEO Analysis Script with human readable output. It can analyze content, media, links, server information, and more, providing a comprehensive overview of a webpage's SEO status - right from your command line.

## Features

- **Content Analysis**: Extracts and evaluates heading tags (H1, H2, H3) for SEO optimization.
- **Media Analysis**: Analyzes images, videos, and audio files for SEO relevance.
- **Link Analysis**: Checks internal and external links, verifies their status, and provides HTTP status codes.
- **Server Information**: Retrieves server details, checks for `sitemap.xml` and `robots.txt`, and validates SSL certificates.
- **Semantic Analysis**: Detects document language, filters out stopwords, and identifies relevant keywords.
- **Google Index Check**: Verifies if the URL is indexed by Google.

## Installation

1. Clone the repository:
    ```bash
    git clone [URL]
    cd seo-cl-analysis
    ```

2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Download NLTK stopwords:
    ```python
    import nltk
    nltk.download('stopwords')
    ```

## Usage

Run the script with the desired parameters:

```bash
python seo-cl-analysis.py --url "http://example.com" [options]
```

### Options

- `--url <URL>`: (Required) The URL to analyze.
- `-f, --follow`: (Recommended) Follow redirects until there are no more.
- `-m, --media`: Analyze media content (video, audio, images) on the page.
- `-l, --links`: Output all internal and external links on the page.
- `-s, --server`: Check for sitemap, robots.txt, SSL certificate status, and server info.
- `-g, --google`: Check if the URL is indexed by Google.
- `-c, --content`: Output heading tags (H1, H2, H3) from the page.
- `-e, --semantic`: Perform semantic analysis on the page content.
- `-a, --all`: Run all checks and outputs (equivalent to setting all parameters).

## Example

To perform a full analysis on a webpage:

```bash
python seo-cl-analysis.py --url "http://example.com" --all
```

To perform only a semantic analysis:

```bash
python seo-cl-analysis.py --url "http://example.com" --semantic
```

## Contributing

Contributions are welcome! Please open an issue to discuss your ideas or create a pull request with your enhancements.

## License

This project is licensed under the MIT License.
