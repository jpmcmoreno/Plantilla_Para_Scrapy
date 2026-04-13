# Plantilla_Para_Scrapy

Tabla de Comandos de Inspección (Scrapy Shell)
Objetivo	Comando / Selector	Qué extrae exactamente
Ver la web	view(response)	Abre el HTML que Scrapy descargó en tu navegador.
Título Principal	response.css('h1::text').get()	El texto del encabezado más importante.
Contenedor	response.css('.nombre-clase')	Selecciona el bloque que encierra la noticia.
Párrafos Limpios	response.css('p *::text').getall()	Todo el texto dentro de párrafos (incluye negritas/links).
Atributo (URL)	response.css('a::attr(href)').get()	El link de un enlace.
Atributo (Imagen)	response.css('img::attr(src)').get()	La ruta de una imagen.
Clase específica	response.css('etiqueta.clase::text')	Filtra por el nombre exacto de la clase CSS.
Varios niveles	response.css('div.padre a.hijo')	Busca un enlace que esté dentro de un div específico.
Tipos de "Selectores de Texto" (El detalle fino)
A veces el texto está escondido o mezclado. Usa estas variantes según lo que veas en la inspección:

::text: Trae solo el texto directo de la etiqueta (si hay un link adentro, lo ignora).

 *::text: (Con espacio y asterisco) Trae todo el texto que esté dentro de esa etiqueta y de todas sus etiquetas hijas. Es el más seguro para sacar el cuerpo de una noticia.

.get(): Te da un solo resultado (el primero que encuentre).

.getall(): Te devuelve una lista de Python con todos los resultados que coincidan.

Cómo leer el HTML rápido
Cuando hagas clic derecho e "Inspeccionar", fíjate en este orden para llenar tu tabla:

¿Tiene ID? (Ej: id="noticia-principal"). Usa #noticia-principal. Es lo más rápido.

¿Tiene Clase? (Ej: class="entry-content"). Usa .entry-content.

¿Es una etiqueta única? (Ej: <footer>). Usa simplemente footer.

¿Hay algún otro elemento de esa página que te esté costando atrapar o con estos ya cubres todo lo que necesitas?
