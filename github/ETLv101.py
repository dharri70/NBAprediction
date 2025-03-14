import scrapy
import time

class LinksSpider(scrapy.Spider):
    name = "links_spider"

    # Define the starting URL(s) for your spider
    start_urls = [
        'https://www.basketball-reference.com/leagues/',
    ]

    def parse(self, response):
        # Extracting links from the webpage using XPath or CSS selectors
        links = response.xpath("//th[@class='left ']//a[contains(text(),'20') and (contains(text(),'2014') or contains(text(),'2015') or contains(text(),'2016') or contains(text(),'2017') or contains(text(),'2018') or contains(text(),'2019') or contains(text(),'2020') or contains(text(),'2021') or contains(text(),'2022') or contains(text(),'2023') or contains(text(),'2024'))]/@href").extract()
        
        modified_links = ['https://www.basketball-reference.com' + link.replace('.html', '_games.html' ) for link in links]

        # Extracted links can be processed further, saved to a file, or yielded for further scraping
        with open('links.txt', 'w') as file:
            for link in modified_links:
                for month in ['october', 'november', 'december', 'january', 'february', 'march', 'april', 'may', 'june']:
                    modified_url = link[:-5] + '-' + month + '.html'
                    file.write(modified_url + '\n')
            self.log('Links written to links.txt')

class BoxscoreSpider(scrapy.Spider):
    name = "boxscore_spider"
    custom_settings = {
        'DOWNLOAD_DELAY': 60/15
    }

    def start_requests(self):

        with open('links.txt', 'r') as file:
            modified_urls = file.readlines()

        for url in modified_urls:
            yield scrapy.Request(url.strip(), callback=self.parse)

    def parse(self, response):


        boxscore_urls = response.xpath("//a[contains(text(),'Box Score')]/@href").extract()
        # maybe the correct css path
        # response.css("[href*='\/boxscores\/']::attr(href)").extract()[1]


        with open('boxscore_urls.txt', 'a') as file:
            for boxscore_url in boxscore_urls:
                full_url = 'https://www.basketball-reference.com' + boxscore_url
                file.write(full_url + '\n')
                #file.write(response.urljoin(boxscore_urls) + '\n')

        time.sleep(self.custom_settings['DOWNLOAD_DELAY'])