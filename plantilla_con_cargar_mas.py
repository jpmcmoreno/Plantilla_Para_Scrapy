# =============================================================================
#  SPIDER PARA SITIOS CON "CARGAR MÁS" O SCROLL INFINITO
#  =============================================================================
#  USO: scrapy runspider spider_elorientalmonagas_ajax.py
#  REQUISITOS: pip install scrapy openpyxl
#
#  ESTE ARCHIVO SIRVE CUANDO:
#    - El sitio tiene un botón "Cargar más" que carga noticias sin recargar
#    - El sitio carga noticias automáticamente al hacer scroll
#    - Ya usaste F12 → Network para descubrir la URL oculta de la API
#
#  ANTES DE USARLO, NECESITAS DESCUBRIR CON F12:
#    1. La URL de la API oculta
#    2. El método (GET o POST)
#    3. Los parámetros que manda el navegador (body)
#    4. Qué campos trae la respuesta JSON (titulo, fecha, url, etc.)
#  =============================================================================

import scrapy
from scrapy.crawler import CrawlerProcess
import openpyxl
from openpyxl.styles import Font
import json  # ← NUEVO: para leer la respuesta JSON del servidor
import os
import re


class ElOrientalMonagasAjaxSpider(scrapy.Spider):
    name = "elorientalmonagas_ajax"
    allowed_domains = ["elorientaldemonagas.com"]

    # ═════════════════════════════════════════════════════════════════════
    # ↓↓↓ PUNTO #1: URL DE LA API OCULTA ↓↓↓
    # ═════════════════════════════════════════════════════════════════════
    # La que descubriste en F12 → Network → Request URL
    # Ejemplo de Emisoras Unidas: "https://emisorasunidas.com/exec/buscador/index.php"
    # ═════════════════════════════════════════════════════════════════════
    API_URL = "https://elorientaldemonagas.com/PON_AQUI_LA_URL_OCULTA"

    # ═════════════════════════════════════════════════════════════════════
    # ↓↓↓ PUNTO #2: CONFIGURACIÓN DE LA PAGINACIÓN ↓↓↓
    # ═════════════════════════════════════════════════════════════════════
    # Estos valores dependen de lo que viste en el Payload de F12.
    # Ajústalos según los nombres reales de los parámetros del sitio.
    # ═════════════════════════════════════════════════════════════════════

    # Cuántas noticias pides por tanda. Empieza con 30 o 50 para probar,
    # luego puedes subirlo a 100 si el servidor lo permite.
    CANTIDAD_POR_TANDA = 30

    # Cuántas tandas máximo pedir. Evita bucles infinitos.
    # Si quieres todas las noticias, ponle un número muy grande (ej: 1000).
    MAX_TANDAS = 50

    # La sección/categoría que quieres scrapear. Este valor depende del sitio.
    # Ejemplo Emisoras Unidas: "nacional"
    CATEGORIA = "politica"

    # Configuración estándar (más lenta porque las APIs suelen ser delicadas)
    custom_settings = {
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "CONCURRENT_REQUESTS": 4,     # más bajo: no queremos saturar la API
        "DOWNLOAD_DELAY": 0.5,
        "DOWNLOAD_TIMEOUT": 20,
        "RETRY_TIMES": 2,
        "LOG_LEVEL": "ERROR",
        "ROBOTSTXT_OBEY": False,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rows = []
        self.visited = set()

    # =========================================================================
    # BLOQUE: start_requests() — PEDIR LA PRIMERA TANDA A LA API
    # =========================================================================
    # Aquí armamos la petición POST manualmente, usando los mismos parámetros
    # que descubriste en F12. La lógica: empezar en "desde=0" y dejar que
    # parse_api() vaya encolando las siguientes tandas.
    # =========================================================================
    def start_requests(self):
        # Empezamos en la tanda 0 (offset = 0)
        yield self._armar_request_api(desde=0, tanda=1)

    # -------------------------------------------------------------------------
    # Función auxiliar que construye una petición a la API
    # -------------------------------------------------------------------------
    def _armar_request_api(self, desde, tanda):
        # ═════════════════════════════════════════════════════════════════
        # ↓↓↓ PUNTO #3: EL BODY DE LA PETICIÓN ↓↓↓
        # ═════════════════════════════════════════════════════════════════
        # Este es el string que viste en F12 → Payload, convertido a formato
        # "clave=valor&clave=valor". Ajusta los nombres según el sitio real.
        #
        # EJEMPLO de Emisoras Unidas:
        #   body = f"por=category&slug={self.CATEGORIA}&desde={desde}&cantidad={self.CANTIDAD_POR_TANDA}"
        #
        # Los nombres "por", "slug", "desde", "cantidad" son los que vimos
        # en su sitio. OTRO sitio puede usar "category", "offset", "limit", etc.
        # Revisa tu Payload y reemplaza los nombres correctos.
        # ═════════════════════════════════════════════════════════════════
        body = (
            f"por=category"
            f"&slug={self.CATEGORIA}"
            f"&desde={desde}"
            f"&cantidad={self.CANTIDAD_POR_TANDA}"
        )

        # Los headers mínimos que el servidor espera. Los saqué del
        # fetch que te copió Chrome en el ejercicio anterior.
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"https://elorientaldemonagas.com/category/{self.CATEGORIA}/",
        }

        # Creamos la Request POST. En Scrapy, para POST usamos el parámetro
        # "body" y especificamos method="POST".
        return scrapy.Request(
            url=self.API_URL,
            method="POST",
            body=body,
            headers=headers,
            callback=self.parse_api,
            # "meta" nos sirve para pasar información entre peticiones,
            # en este caso para recordar en qué tanda vamos.
            meta={"desde": desde, "tanda": tanda},
        )

    # =========================================================================
    # BLOQUE: parse_api() — PROCESAR LA RESPUESTA JSON DE LA API
    # =========================================================================
    def parse_api(self, response):
        # La respuesta viene en formato JSON. Lo convertimos a un diccionario
        # de Python con json.loads(). "response.text" es el string crudo.
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            # Si la respuesta no es JSON válido, algo falló. Salimos.
            return

        # ═════════════════════════════════════════════════════════════════
        # ↓↓↓ PUNTO #4: LEER LA RESPUESTA ↓↓↓
        # ═════════════════════════════════════════════════════════════════
        # Aquí depende de cómo el servidor estructura su respuesta JSON.
        # En Emisoras Unidas era así:
        #   data = {
        #     "statusCode": 200,
        #     "totalFound": "55910",
        #     "numrows": 6,
        #     "result": [ {id, titulo, fecha, url, ...}, ... ]
        #   }
        #
        # AJUSTA las siguientes líneas según los nombres reales del JSON
        # que descubras con F12 → Response.
        # ═════════════════════════════════════════════════════════════════

        # Extraemos la lista de noticias
        noticias = data.get("result", [])

        # Si no hay noticias, significa que llegamos al final. Paramos.
        if not noticias:
            return

        # Recorremos cada noticia y extraemos los campos
        for noticia in noticias:
            # ↓↓↓ AJUSTA estos nombres de campo según tu JSON real ↓↓↓
            titular = noticia.get("titulo", "")        # o "title"
            link = noticia.get("url", "")              # o "link", "permalink"
            fecha = noticia.get("fecha", "")           # o "date", "published"
            cuerpo = noticia.get("descripcion", "")    # o "content", "excerpt"

            # Limpieza básica del cuerpo si viene con HTML
            cuerpo = re.sub(r"<[^>]+>", "", cuerpo)    # quita etiquetas HTML
            cuerpo = re.sub(r"\s+", " ", cuerpo).strip()

            # Evitar duplicados
            if link and link not in self.visited:
                self.visited.add(link)
                self.rows.append({
                    "titular": titular,
                    "link": link,
                    "fecha": fecha,
                    "cuerpo_noticia": cuerpo,
                })

        # ─────────────────────────────────────────────────────────────────
        # ENCOLAR LA SIGUIENTE TANDA
        # ─────────────────────────────────────────────────────────────────
        tanda_actual = response.meta["tanda"]
        desde_actual = response.meta["desde"]
        siguiente_desde = desde_actual + self.CANTIDAD_POR_TANDA
        siguiente_tanda = tanda_actual + 1

        # Solo seguimos si no hemos llegado al máximo de tandas
        if siguiente_tanda <= self.MAX_TANDAS:
            yield self._armar_request_api(
                desde=siguiente_desde,
                tanda=siguiente_tanda,
            )

    # =========================================================================
    # BLOQUE: closed() — GENERAR EL EXCEL AL TERMINAR
    # Idéntico al otro spider, no lo necesitas modificar.
    # =========================================================================
    def closed(self, reason):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Noticias"

        headers = ["titular", "link", "fecha", "cuerpo_noticia"]
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)

        for row in self.rows:
            ws.append([row["titular"], row["link"], row["fecha"], row["cuerpo_noticia"]])

        ws.column_dimensions["A"].width = 60
        ws.column_dimensions["B"].width = 50
        ws.column_dimensions["C"].width = 22
        ws.column_dimensions["D"].width = 120
        ws.freeze_panes = "A2"

        path = os.path.abspath("elorientalmonagas_resultados.xlsx")
        wb.save(path)
        print(f"\n✅ Listo. {len(self.rows)} noticias guardadas en: {path}")


if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(ElOrientalMonagasAjaxSpider)
    process.start()
