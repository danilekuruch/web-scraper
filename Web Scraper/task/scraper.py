import shutil
import re
import requests
from bs4 import BeautifulSoup
import string
import os
from itertools import chain

TXT_EXTENSION = ".txt"
BASE_URL = "https://www.nature.com"


def sanitize_filename(name: str) -> str:
    return name.translate(str.maketrans("", "", string.punctuation)).replace(" ", "_")


def get_file_name(name: str) -> str:
    return sanitize_filename(name) + TXT_EXTENSION


def get_file_path(dir_name, file_name):
    return os.path.join(dir_name, file_name)


def get_soup(url: str) -> BeautifulSoup | None:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.RequestException:
        return None


def check_dir(dir_name: str):
    if os.path.exists(dir_name):
        shutil.rmtree(dir_name)
    os.mkdir(dir_name)


def save_file(dir_name, file_name, content):
    file_path = get_file_path(dir_name, get_file_name(file_name))
    with open(file_path, "w", encoding="utf-8") as f:
        print(content, file=f, flush=True)
    return file_path


def analyze_page(page, article_type):
    return (
        link_tag.get("href")
        for article in page.find_all("article")
        if (t := article.find("span", attrs={"data-test": "article.type"}))
           and t.text.strip() == article_type
           and (link_tag := article.find("a", attrs={"data-track-action": "view article"}))
    )


def analyze_article(article_soup):
    content = article_soup.find(class_=re.compile("article__teaser"))
    title = article_soup.find("title")
    return (title.text, content.text) if content and title else None


def get_page_info(page_number):
    return f"Page_{page_number}", get_soup(f"{BASE_URL}/nature/articles?sort=PubDate&year=2020&page={page_number}")


def main():
    amount_page = int(input("Number of pages: "))
    article_type = input("Article type: ")

    # Prepare pages
    pages = tuple(
        get_page_info(page_number)
        for page_number in range(1, amount_page + 1)
    )

    # Ensure directories
    tuple(map(lambda page: check_dir(page[0]), pages))

    # Collect article links
    article_links = chain.from_iterable(
        analyze_page(page_soup, article_type)
        for _, page_soup in pages
        if page_soup
    )

    # Download article soups
    article_soups = (
        article_soup
        for link in article_links
        if (article_soup := get_soup(BASE_URL + link))
    )

    # Extract and save
    files = tuple(
        save_file(dir_name, *data)
        for (dir_name, page_soup), soup in zip(pages, article_soups)
        if page_soup and (data := analyze_article(soup))
    )

    print(files)


if __name__ == "__main__":
    main()
