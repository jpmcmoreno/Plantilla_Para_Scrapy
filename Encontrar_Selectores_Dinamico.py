"""
╔══════════════════════════════════════════════════════════════╗
║              🔍 SELECTOR FINDER - Web Scraping Helper       ║
║  Abre una página, haz click en cualquier elemento y         ║
║  obtén su selector CSS/XPath listo para Scrapy o Selenium.  ║
╚══════════════════════════════════════════════════════════════╝

Requisitos:
    pip install playwright
    playwright install chromium
"""

import asyncio
from playwright.async_api import async_playwright

# ── JavaScript inyectado en la página ──────────────────────────
# Genera selectores CSS y XPath al hacer click en cualquier elemento.
INJECTED_JS = """
(() => {
    // Evitar inyectar dos veces
    if (window.__selectorFinderActive) return;
    window.__selectorFinderActive = true;

    // ── Estilo visual del hover / selección ──
    const style = document.createElement('style');
    style.textContent = `
        .__sf-hover {
            outline: 2px dashed #e74c3c !important;
            outline-offset: 2px !important;
            cursor: crosshair !important;
        }
        .__sf-selected {
            outline: 3px solid #2ecc71 !important;
            outline-offset: 2px !important;
        }
        #__sf-tooltip {
            position: fixed;
            bottom: 12px;
            left: 50%;
            transform: translateX(-50%);
            background: #1a1a2e;
            color: #0f0;
            font-family: 'Consolas', 'Fira Code', monospace;
            font-size: 13px;
            padding: 10px 18px;
            border-radius: 8px;
            z-index: 2147483647;
            pointer-events: none;
            white-space: pre;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            border: 1px solid #333;
            max-width: 90vw;
            overflow: hidden;
            text-overflow: ellipsis;
        }
    `;
    document.head.appendChild(style);

    // Tooltip flotante
    const tooltip = document.createElement('div');
    tooltip.id = '__sf-tooltip';
    tooltip.textContent = '🔍 Haz click en cualquier elemento para obtener su selector';
    document.body.appendChild(tooltip);

    // ── Generar selector CSS óptimo ──
    function getCssSelector(el) {
        if (el.id) return `#${CSS.escape(el.id)}`;

        const parts = [];
        let current = el;

        while (current && current !== document.body && current !== document.documentElement) {
            let selector = current.tagName.toLowerCase();

            // Intentar con id
            if (current.id) {
                parts.unshift(`#${CSS.escape(current.id)} `);
                break;
            }

            // Clases relevantes (filtrar clases internas del finder)
            const classes = Array.from(current.classList)
                .filter(c => !c.startsWith('__sf-'))
                .map(c => `.${CSS.escape(c)}`);

            if (classes.length > 0) {
                selector += classes.slice(0, 3).join('');
                // Si es único con las clases, parar
                const test = [...(current.parentElement?.querySelectorAll(selector) || [])];
                if (test.length === 1) {
                    parts.unshift(selector);
                    break;
                }
            }

            // nth-child como fallback
            if (current.parentElement) {
                const siblings = Array.from(current.parentElement.children)
                    .filter(s => s.tagName === current.tagName);
                if (siblings.length > 1) {
                    const idx = siblings.indexOf(current) + 1;
                    selector += `:nth-child(${idx})`;
                }
            }

            parts.unshift(selector);
            current = current.parentElement;
        }

        return parts.join(' > ');
    }

    // ── Generar XPath ──
    function getXPath(el) {
        if (el.id) return `//*[@id="${el.id}"]`;

        const parts = [];
        let current = el;

        while (current && current.nodeType === Node.ELEMENT_NODE) {
            let tag = current.tagName.toLowerCase();

            if (current.id) {
                parts.unshift(`//*[@id="${current.id}"]`);
                return parts.join('/');
            }

            if (current.parentElement) {
                const siblings = Array.from(current.parentElement.children)
                    .filter(s => s.tagName === current.tagName);
                if (siblings.length > 1) {
                    const idx = siblings.indexOf(current) + 1;
                    tag += `[${idx}]`;
                }
            }

            parts.unshift(tag);
            current = current.parentElement;
        }

        return '/' + parts.join('/');
    }

    // ── Obtener atributos útiles ──
    function getAttributes(el) {
        const attrs = {};
        const dominated = ['href', 'src', 'alt', 'title', 'name', 'data-id',
                          'data-testid', 'aria-label', 'placeholder', 'type', 'value', 'role'];
        for (const name of dominated) {
            if (el.hasAttribute(name)) {
                const val = el.getAttribute(name);
                if (val) attrs[name] = val.length > 80 ? val.slice(0, 80) + '…' : val;
            }
        }
        return attrs;
    }

    // ── Eventos ──
    let lastHovered = null;

    document.addEventListener('mouseover', (e) => {
        if (lastHovered) lastHovered.classList.remove('__sf-hover');
        e.target.classList.add('__sf-hover');
        lastHovered = e.target;

        const tag = e.target.tagName.toLowerCase();
        const cls = Array.from(e.target.classList).filter(c => !c.startsWith('__sf-')).join('.');
        tooltip.textContent = `🔍 <${tag}${cls ? '.' + cls : ''}> — click para inspeccionar`;
    }, true);

    document.addEventListener('mouseout', (e) => {
        e.target.classList.remove('__sf-hover');
    }, true);

    document.addEventListener('click', (e) => {
        // Ignorar elementos propios del finder
        if (e.target.id === '__sf-tooltip') return;

        e.preventDefault();
        e.stopPropagation();

        const el = e.target;

        // Quitar selección anterior
        document.querySelectorAll('.__sf-selected').forEach(
            s => s.classList.remove('__sf-selected')
        );
        el.classList.add('__sf-selected');

        const css = getCssSelector(el);
        const xpath = getXPath(el);
        const text = (el.textContent || '').trim().slice(0, 100);
        const tag = el.tagName.toLowerCase();
        const attrs = getAttributes(el);

        // Construir el mensaje para la consola de Python
        const payload = JSON.stringify({
            type: '__selector_result__',
            tag,
            css,
            xpath,
            text: text || null,
            attributes: attrs
        });

        console.log(payload);

        // Actualizar tooltip
        tooltip.textContent = `✅ ${css}`;
    }, true);
})();
"""


# ── Colores para la terminal ──
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    GREEN  = "\033[38;5;82m"
    CYAN   = "\033[38;5;39m"
    YELLOW = "\033[38;5;220m"
    ORANGE = "\033[38;5;208m"
    PURPLE = "\033[38;5;141m"
    RED    = "\033[38;5;196m"
    GRAY   = "\033[38;5;245m"
    WHITE  = "\033[38;5;255m"
    BG     = "\033[48;5;235m"


def print_banner():
    print(f"""
{C.CYAN}{C.BOLD}╔══════════════════════════════════════════════════════════════╗
║              🔍  SELECTOR FINDER  v1.0                      ║
║         Herramienta de selectores para Web Scraping         ║
╚══════════════════════════════════════════════════════════════╝{C.RESET}
""")


def print_selector_result(data: dict):
    """Imprime los selectores de forma bonita en la terminal."""
    tag = data.get("tag", "?")
    css = data.get("css", "")
    xpath = data.get("xpath", "")
    text = data.get("text")
    attrs = data.get("attributes", {})

    print(f"\n{C.GREEN}{C.BOLD}{'━' * 64}{C.RESET}")
    print(f"  {C.YELLOW}{C.BOLD}📌 Elemento: {C.WHITE}<{tag}>{C.RESET}")
    if text:
        display_text = text[:80] + "…" if len(text) > 80 else text
        print(f"  {C.GRAY}📝 Texto:    \"{display_text}\"{C.RESET}")

    if attrs:
        print(f"  {C.GRAY}🏷️  Atributos:{C.RESET}")
        for k, v in attrs.items():
            print(f"     {C.DIM}{k}={C.RESET}\"{v}\"")

    print()
    print(f"  {C.CYAN}{C.BOLD}🎯 Scrapy CSS:{C.RESET}")
    print(f"     {C.WHITE}response.css({C.GREEN}\"{css}::text\"{C.WHITE}){C.RESET}")
    print(f"     {C.WHITE}response.css({C.GREEN}\"{css}::attr(href)\"{C.WHITE}){C.RESET}")

    if css:
        print()
        print(f"  {C.PURPLE}{C.BOLD}🎯 Scrapy XPath:{C.RESET}")
        print(f"     {C.WHITE}response.xpath({C.GREEN}'{xpath}/text()'{C.WHITE}){C.RESET}")
        print(f"     {C.WHITE}response.xpath({C.GREEN}'{xpath}/@href'{C.WHITE}){C.RESET}")

    print()
    print(f"  {C.ORANGE}{C.BOLD}🎯 Selenium / Playwright:{C.RESET}")
    print(f"     {C.WHITE}driver.find_element(By.CSS_SELECTOR, {C.GREEN}\"{css}\"{C.WHITE}){C.RESET}")
    print(f"     {C.WHITE}page.locator({C.GREEN}\"{css}\"{C.WHITE}){C.RESET}")

    if "href" in attrs:
        print()
        print(f"  {C.GRAY}🔗 Link: {attrs['href']}{C.RESET}")

    print(f"{C.GREEN}{C.BOLD}{'━' * 64}{C.RESET}")
    print(f"  {C.DIM}Haz click en otro elemento o cierra el navegador para salir{C.RESET}\n")


async def main():
    print_banner()

    url = input(f"  {C.CYAN}{C.BOLD}🌐 Ingresa la URL a inspeccionar:{C.RESET} ").strip()

    if not url:
        print(f"  {C.RED}❌ No ingresaste ninguna URL.{C.RESET}")
        return

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    print(f"\n  {C.YELLOW}⏳ Abriendo navegador...{C.RESET}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        # Escuchar mensajes de consola del JS inyectado
        def on_console(msg):
            text = msg.text
            if '"type":"__selector_result__"' in text or '"type": "__selector_result__"' in text:
                import json
                try:
                    data = json.loads(text)
                    print_selector_result(data)
                except json.JSONDecodeError:
                    pass

        page.on("console", on_console)

        try:
            print(f"  {C.YELLOW}⏳ Cargando: {url}{C.RESET}")
            await page.goto(url, wait_until="domcontentloaded", timeout=120000)
            print(f"  {C.GREEN}✅ Página cargada correctamente.{C.RESET}")
        except Exception as e:
            print(f"  {C.RED}❌ Error al cargar la página: {e}{C.RESET}")
            await browser.close()
            return

        # Inyectar el JS inspector
        await page.evaluate(INJECTED_JS)

        # Re-inyectar en cada navegación dentro de la página
        page.on("load", lambda _: asyncio.ensure_future(
            page.evaluate(INJECTED_JS).catch(lambda _: None) if not page.is_closed() else asyncio.sleep(0)
        ))

        print(f"""
  {C.CYAN}{C.BOLD}┌─────────────────────────────────────────────────┐
  │  🖱️  Haz click en cualquier elemento de la     │
  │     página para ver su selector aquí.           │
  │                                                 │
  │  🔄  Navega libremente por la página.           │
  │  ❌  Cierra el navegador para terminar.         │
  └─────────────────────────────────────────────────┘{C.RESET}
""")

        # Mantener vivo hasta que se cierre el navegador
        try:
            await page.wait_for_event("close", timeout=0)
        except Exception:
            pass

        try:
            await browser.close()
        except Exception:
            pass

    print(f"\n  {C.CYAN}👋 ¡Hasta luego! Happy scraping 🕷️{C.RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())
