import requests
from bs4 import BeautifulSoup
import csv
import datetime
import re

mainpath = 'https://stocktwits.com/markets/news/crypto'


def initialize_csv():
    with open('stocktwits_news.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Title', 'Abstract', 'Source', 'Published At', 'Link'])

def crawl_stocktwits_news():
    news_list = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    page_num = 1
    while True:
        page_url = f"{mainpath}?page={page_num}"
        response = requests.get(page_url, headers=headers)

        if response.status_code == 200:
            new_news, oldest_published_at = parse_page(response)
            if not new_news or oldest_published_at < datetime.datetime.now() - datetime.timedelta(hours=48):
                break
            news_list.extend(new_news)
            page_num += 1
        else:
            print(f"Failed to retrieve page {page_num}. Status code: {response.status_code}")
            break

    return news_list

def parse_page(response):
    soup = BeautifulSoup(response.content, 'html.parser')
    news_items = soup.find_all('div', class_='NewsItem_container__w30_A')

    parsed_news = []
    oldest_published_at = datetime.datetime.now()

    for item in news_items:
        title_element = item.find('a', class_='NewsItem_title__QTvqJ')
        title = title_element.text.strip() if title_element else "N/A"

        abstract_element = item.find('div', class_='NewsItem_description__yWGa3')
        abstract = abstract_element.text.strip() if abstract_element else "N/A"

        source_element = item.find('span', class_='mr-2')
        source = source_element.text.strip() if source_element else "N/A"

        date_element = source_element.find_next_sibling('span')
        date_str = date_element.text.strip() if date_element else "N/A"
        published_at = parse_published_date(date_str)

        link_element = item.find('a', class_='NewsItem_title__QTvqJ', href=True)
        link = link_element['href'] if link_element else "N/A"

        if published_at >= datetime.datetime.now() - datetime.timedelta(hours=48):
            news_item = {
                'Title': title,
                'Abstract': abstract,
                'Source': source,
                'Published At': published_at,
                'Link': link
            }
            parsed_news.append(news_item)

            # Track the oldest published date to determine when to stop crawling
            if published_at < oldest_published_at:
                oldest_published_at = published_at

    return parsed_news, oldest_published_at

def parse_published_date(date_str):
    # Example date_str formats: '17 minutes ago', 'an hour ago', '2022-07-15 12:30:45'
    now = datetime.datetime.now()

    if 'minute' in date_str:
        minutes = int(re.search(r'\d+', date_str).group())
        return now - datetime.timedelta(minutes=minutes)
    elif 'hour' in date_str:
        hours = int(re.search(r'\d+', date_str).group())
        return now - datetime.timedelta(hours=hours)
    else:
        try:
            return datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return now  # Fallback to current time if parsing fails

def write_to_csv(news_list):
    with open('stocktwits_news.csv', 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['Title', 'Abstract', 'Source', 'Published At', 'Link'])
        for news in news_list:
            writer.writerow(news)


if __name__ == "__main__":
    initialize_csv()
    news_list = crawl_stocktwits_news()
    write_to_csv(news_list)
    print(f"CSV file 'stocktwits_news.csv' has been created with {len(news_list)} news items.")
