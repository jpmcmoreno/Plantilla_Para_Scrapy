# =============================================================================
#  SPIDER PARA EL ORIENTAL DE MONAGAS — paginación HTML clásica
#  =============================================================================
#  USO: scrapy runspider spider_elorientalmonagas.py
#  REQUISITOS: pip install scrapy openpyxl
#
#  ESTE ARCHIVO SIRVE PARA SITIOS QUE:
#    - Tienen secciones con URL tipo /politica/, /deportes/, etc.
#    - Tienen paginación con botones "siguiente" o "página 2, 3, 4..."
#    - NO usan "Cargar más" ni scroll infinito
#  =============================================================================

# -----------------------------------------------------------------------------
# BLOQUE 1: IMPORTS
# -----------------------------------------------------------------------------
# "import" significa "tráeme esta herramienta para poder usarla".
# Son las librerías externas que el spider necesita para funcionar.
# NO TOCAR ESTA PARTE, es igual para todos los spiders.

import scrapy                          # la librería principal para scrapear
from scrapy.crawler import CrawlerProcess  # para poder ejecutar con "python archivo.py"
import openpyxl                        # para crear el archivo Excel al final
from openpyxl.styles import Font       # para poner la cabecera del Excel en negrita
import os                              # para manejar rutas de archivos del sistema
import re                              # para limpiar espacios en el cuerpo con "regex"


# -----------------------------------------------------------------------------
# BLOQUE 2: DEFINICIÓN DE LA CLASE DEL SPIDER
# -----------------------------------------------------------------------------
# Una "clase" en Python es como un molde que contiene datos + funciones.
# Scrapy necesita que tu spider sea una clase que herede de "scrapy.Spider".
# "Hereda de" significa que ya trae un montón de funcionalidad gratis por defecto.

class ElOrientalMonagasSpider(scrapy.Spider):

    # El "name" es un identificador interno del spider. Ponle el que quieras,
    # pero que sea corto y sin espacios. Sirve por si en el futuro lo ejecutas
    # desde un proyecto Scrapy más grande.
    name = "elorientalmonagas"

    # "allowed_domains" es una lista blanca: el spider NO visitará URLs fuera
    # de este dominio. Es una medida de seguridad para que no se te escape a
    # Facebook, Twitter o sitios que enlaza el periódico.
    allowed_domains = ["elorientaldemonagas.com"]

    # ═════════════════════════════════════════════════════════════════════
    # ↓↓↓ PUNTO #1 PARA RELLENAR: URLs DE INICIO ↓↓↓
    # ═════════════════════════════════════════════════════════════════════
    # Aquí van las URLs desde las que el spider empezará a trabajar.
    # TÍPICAMENTE son las secciones del periódico.
    #
    # CÓMO LLENARLO:
    #   1. Ve a https://elorientaldemonagas.com/
    #   2. Mira el menú de arriba: ¿qué secciones hay? (Política, Deportes...)
    #   3. Haz click en cada una y copia la URL exacta
    #   4. Pégala aquí, una por línea, entre comillas, separadas por comas
    #
    # EJEMPLO FICTICIO (el tuyo será distinto):
    #   "https://elorientaldemonagas.com/politica/",
    #   "https://elorientaldemonagas.com/sucesos/",
    #   "https://elorientaldemonagas.com/deportes/",
    # ═════════════════════════════════════════════════════════════════════
    start_urls = [
        "https://elorientaldemonagas.com/",
        # ← agrega más secciones aquí, una por línea
    ]

    # -------------------------------------------------------------------------
    # BLOQUE 3: CONFIGURACIÓN DEL SPIDER
    # -------------------------------------------------------------------------
    # Aquí le dices a Scrapy cómo comportarse: qué velocidad, qué "disfraz"
    # usar, cuánto esperar, etc. PUEDES DEJAR ESTO TAL CUAL para empezar.
    custom_settings = {
        # USER_AGENT = el "disfraz" del navegador. Con esto le decimos al
        # servidor "soy Chrome en Windows". Si no lo pones, Scrapy se
        # identifica como "Scrapy bot" y algunos sitios bloquean eso.
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        # Cuántas peticiones hace al mismo tiempo. 16 es razonable: rápido
        # pero sin abusar del servidor.
        "CONCURRENT_REQUESTS": 16,
        # Cuánto espera entre peticiones (en segundos). 0.3 = muy rápido.
        # Si el sitio te bloquea, sube a 1 o 2.
        "DOWNLOAD_DELAY": 0.3,
        # Cuánto espera a que el servidor responda antes de rendirse.
        "DOWNLOAD_TIMEOUT": 15,
        # Cuántas veces reintenta si falla una petición.
        "RETRY_TIMES": 2,
        # Qué nivel de mensajes muestra. ERROR = solo errores graves.
        # Si quieres ver TODO lo que hace, cámbialo a "DEBUG".
        "LOG_LEVEL": "ERROR",
        # Ignorar el archivo robots.txt del sitio. Ponlo en False solo si
        # scrapeas con fines periodísticos o académicos.
        "ROBOTSTXT_OBEY": False,
    }

    # -------------------------------------------------------------------------
    # BLOQUE 4: INICIALIZACIÓN
    # -------------------------------------------------------------------------
    # __init__ es una función especial que se ejecuta UNA VEZ al crear el
    # spider. Aquí preparamos las "cajas vacías" donde iremos guardando
    # cosas mientras el spider trabaja.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # llama al __init__ original de Scrapy

        # self.rows será la lista donde acumulamos todas las noticias.
        # Cada noticia será un diccionario con titular, link, fecha, cuerpo.
        self.rows = []

        # self.visited es un "set" (conjunto sin duplicados) que recuerda
        # qué URLs ya visitamos, para no procesar la misma noticia dos veces.
        self.visited = set()

    # =========================================================================
    # BLOQUE 5: parse() — PROCESAR UNA PÁGINA DE LISTADO (SECCIÓN)
    # =========================================================================
    # Esta función se ejecuta cuando llega el HTML de una de las start_urls.
    # Su trabajo es:
    #   1. Encontrar los enlaces a las noticias individuales
    #   2. Encolar cada noticia para procesarla en parse_article()
    #   3. Encontrar el enlace a la siguiente página y encolarlo también
    # =========================================================================
    def parse(self, response):
        # "response" es el objeto que contiene el HTML descargado + la URL.
        # Tiene un método .css() que te permite buscar cosas con selectores.

        # ═════════════════════════════════════════════════════════════════
        # ↓↓↓ PUNTO #2 PARA RELLENAR: SELECTOR DE LINKS EN EL LISTADO ↓↓↓
        # ═════════════════════════════════════════════════════════════════
        # CÓMO LLENARLO:
        #   1. Abre una sección del periódico (ej: /politica/)
        #   2. Aprieta F12 → pestaña Elements
        #   3. Click en la flechita (cursor con cuadrito) arriba a la izq
        #   4. Click en el TITULAR de la primera noticia del listado
        #   5. Mira el HTML que te resaltó: busca el <h1>, <h2> o <h3>
        #      que contiene el título, y mira qué CLASE tiene.
        #
        # PATRONES COMUNES EN WORDPRESS (casi todos los periódicos usan WP):
        #   "h2.entry-title a::attr(href)"       ← el más clásico
        #   "article h2 a::attr(href)"           ← articulos con h2 dentro
        #   "h3.entry-title a::attr(href)"       ← algunas themes usan h3
        #   ".post-title a::attr(href)"          ← otras themes
        #
        # EL ::attr(href) SIGNIFICA: "del enlace <a>, dame el valor del href"
        # ═════════════════════════════════════════════════════════════════
        links = response.css("h2 a::attr(href)").getall()

        # Recorremos la lista de links encontrados
        for link in links:
            # urljoin convierte un link relativo (/politica/noticia) a
            # absoluto (https://elorientaldemonagas.com/politica/noticia).
            # Si ya es absoluto, lo deja igual.
            url = response.urljoin(link)

            # Si nunca lo visitamos, lo marcamos y lo encolamos.
            if url not in self.visited:
                self.visited.add(url)
                # "yield" es como "return" pero para generadores.
                # Le está diciendo a Scrapy: "por favor ve a esta URL y
                # cuando tengas la respuesta, pásala a parse_article".
                yield scrapy.Request(url, callback=self.parse_article)

        # ═════════════════════════════════════════════════════════════════
        # ↓↓↓ PUNTO #3 PARA RELLENAR: SELECTOR DE PAGINACIÓN ↓↓↓
        # ═════════════════════════════════════════════════════════════════
        # CÓMO LLENARLO:
        #   1. Baja al final de la sección en el navegador
        #   2. Busca el botón "Siguiente" o "Next" o una flecha →
        #   3. Con F12, inspecciona ese botón
        #   4. Mira qué clase tiene o si tiene rel="next"
        #
        # PATRONES COMUNES:
        #   "a.next::attr(href)"                  ← clase "next"
        #   'a[rel="next"]::attr(href)'           ← con rel="next" (muy común)
        #   "a.next.page-numbers::attr(href)"     ← WordPress clásico
        #   ".pagination a.next::attr(href)"      ← dentro de un div pagination
        # ═════════════════════════════════════════════════════════════════
        next_page = response.css("a.next::attr(href)").get()
        if next_page:
            # Si encontramos siguiente página, la convertimos a URL absoluta
            # y la encolamos para procesarla con esta MISMA función parse().
            # Por eso decimos callback=self.parse (no parse_article).
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse)

    # =========================================================================
    # BLOQUE 6: parse_article() — PROCESAR UNA NOTICIA INDIVIDUAL
    # =========================================================================
    # Esta función se ejecuta cuando llega el HTML de una noticia.
    # Su trabajo es extraer titular, fecha y cuerpo, y guardarlos en self.rows.
    # =========================================================================
    def parse_article(self, response):

        # ═════════════════════════════════════════════════════════════════
        # ↓↓↓ PUNTO #4 PARA RELLENAR: SELECTOR DEL TITULAR ↓↓↓
        # ═════════════════════════════════════════════════════════════════
        # CÓMO LLENARLO:
        #   1. Abre CUALQUIER noticia del periódico
        #   2. F12 → inspecciona el titular grande
        #   3. Mira qué etiqueta y qué clase tiene el <h1>
        #
        # El código de abajo ya tiene fallbacks: intenta con un selector
        # específico, si falla usa uno genérico, si falla usa el <meta>.
        # Solo cambia el PRIMER selector si conoces el bueno; los otros
        # déjalos como están por seguridad.
        # ═════════════════════════════════════════════════════════════════
        titular = (
            response.css("h1.entry-title::text").get()         # específico
            or response.css("h1::text").get()                  # cualquier h1
            or response.css('meta[property="og:title"]::attr(content)').get()  # meta
            or ""
        ).strip()  # .strip() quita espacios en blanco al inicio y final

        # ═════════════════════════════════════════════════════════════════
        # ↓↓↓ PUNTO #5 PARA RELLENAR: SELECTOR DE LA FECHA ↓↓↓
        # ═════════════════════════════════════════════════════════════════
        # La fecha es la parte más variable: cada sitio la pone diferente.
        # Por eso intentamos varios fallbacks.
        #
        # FUENTES POSIBLES DE FECHA (en orden de confiabilidad):
        #   1. <time datetime="2026-04-11">  ← lo MÁS confiable si existe
        #   2. <meta property="article:published_time">  ← casi siempre hay
        #   3. Un <span class="date"> con texto visible
        #
        # Si ninguno de los dos selectores de abajo funciona, puedes añadir
        # un tercero: response.css("span.date::text").get()
        # ═════════════════════════════════════════════════════════════════
        fecha = (
            response.css("time::attr(datetime)").get()
            or response.css('meta[property="article:published_time"]::attr(content)').get()
            or ""
        ).strip()

        # ═════════════════════════════════════════════════════════════════
        # ↓↓↓ PUNTO #6 PARA RELLENAR: SELECTOR DEL CUERPO ↓↓↓
        # ═════════════════════════════════════════════════════════════════
        # Para el cuerpo buscamos TODOS los <p> que están dentro del div
        # contenedor de la noticia. El truco es saber qué div los contiene.
        #
        # CÓMO LLENARLO:
        #   1. En una noticia, F12 → inspecciona el PRIMER párrafo
        #   2. Sube en el árbol de HTML (en el panel de F12) hasta encontrar
        #      el <div> que agrupa todos los párrafos
        #   3. Mira qué clase tiene ese <div>
        #
        # CONTENEDORES COMUNES EN WORDPRESS:
        #   "div.entry-content"       ← el más común
        #   "div.post-content"
        #   "div.single-content"
        #   "article .content"
        # ═════════════════════════════════════════════════════════════════
        parrafos = (
            response.css("div.entry-content p::text").getall()  # específico
            or response.css("article p::text").getall()         # genérico 1
            or response.css("p::text").getall()                 # último recurso
        )
        # Unimos todos los párrafos en un solo texto, separados por espacios
        cuerpo = " ".join(p.strip() for p in parrafos if p.strip())
        # Limpiamos espacios múltiples (más de un espacio seguido) con regex
        cuerpo = re.sub(r"\s+", " ", cuerpo).strip()

        # Solo guardamos la noticia si al menos tiene titular.
        # Si no hay titular probablemente la página no es una noticia válida.
        if titular:
            self.rows.append({
                "titular": titular,
                "link": response.url,
                "fecha": fecha,
                "cuerpo_noticia": cuerpo,
            })

    # =========================================================================
    # BLOQUE 7: closed() — SE EJECUTA AL TERMINAR TODO
    # =========================================================================
    # Scrapy llama a esta función cuando el spider termina. Aquí generamos
    # el archivo Excel con todas las noticias acumuladas en self.rows.
    # ESTA PARTE NO LA NECESITAS MODIFICAR, es igual para todos los spiders.
    # =========================================================================
    def closed(self, reason):
        wb = openpyxl.Workbook()  # crea un nuevo archivo Excel en memoria
        ws = wb.active            # toma la primera hoja por defecto
        ws.title = "Noticias"     # le pone nombre a la pestaña

        # Crea la fila de encabezados
        headers = ["titular", "link", "fecha", "cuerpo_noticia"]
        ws.append(headers)
        # Pone la cabecera en negrita
        for cell in ws[1]:
            cell.font = Font(bold=True)

        # Agrega cada noticia como una fila
        for row in self.rows:
            ws.append([row["titular"], row["link"], row["fecha"], row["cuerpo_noticia"]])

        # Ajusta anchos de columna para que sea legible
        ws.column_dimensions["A"].width = 60   # titular
        ws.column_dimensions["B"].width = 50   # link
        ws.column_dimensions["C"].width = 22   # fecha
        ws.column_dimensions["D"].width = 120  # cuerpo
        ws.freeze_panes = "A2"  # fija la cabecera al hacer scroll

        # Guarda el archivo en la carpeta actual
        path = os.path.abspath("elorientalmonagas_resultados.xlsx")
        wb.save(path)
        print(f"\n✅ Listo. {len(self.rows)} noticias guardadas en: {path}")


# -----------------------------------------------------------------------------
# BLOQUE 8: PUNTO DE ENTRADA
# -----------------------------------------------------------------------------
# Esto permite ejecutar el script con "python spider_elorientalmonagas.py"
# sin necesidad de usar el comando "scrapy runspider".
if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(ElOrientalMonagasSpider)
    process.start()
