import scrapy

class BasketballReferenceSpider(scrapy.Spider):
    name = "basketball_reference_spider"
    start_urls = [
        'https://www.basketball-reference.com/boxscores/202112010IND.html',
    ]


    def parse(self, response):
        # Extract the text from the specified CSS selector
        # Using XPath
        # Using CSS Selector
        link_text = response.xpath("/html//table[@id='four_factors']").extract()



        
        # Write the extracted player names to a text file
        with open('please_say_atl.txt', 'w') as file:
           if link_text:
              file.write(link_text)
           else:
               file.write('Better luck next time.')
               

