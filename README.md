# Plantilla_Para_Scrapy

<img width="732" height="622" alt="image" src="https://github.com/user-attachments/assets/9764246a-870c-40df-8e7a-c5ef2fe178e9" />

<img width="726" height="487" alt="image" src="https://github.com/user-attachments/assets/108744ba-7b53-429c-a2c4-b7e44aa4d36f" />

<img width="775" height="791" alt="image" src="https://github.com/user-attachments/assets/d251361e-7a96-4e2c-8d09-0c92233817e1" />

<img width="1478" height="810" alt="image" src="https://github.com/user-attachments/assets/086ed4be-9d8e-46da-830e-2c8510e65b1f" />


import scrapy

class NoticiaSpider(scrapy.Spider):
    name = "noticias"
    allowed_domains = ["elorientaldemonagas.com"]
    start_urls = ["https://elorientaldemonagas.com/atletico-la-cruz-listo-para-el-torneo-apertura-2024/"]

    def parse(self, response):
        # Seccion de extracción (lo que probamos en el shell)
        yield {
            'titulo': response.css('h1.entry-title::text').get(),
            'cuerpo': "\n".join(response.css('.entry-content p *::text').getall()),
            'url_original': response.url
        }

  <img width="1448" height="537" alt="image" src="https://github.com/user-attachments/assets/2faa80ae-beb7-4d68-917f-6498fd49f984" />
