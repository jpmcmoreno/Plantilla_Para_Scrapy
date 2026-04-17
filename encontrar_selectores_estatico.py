"""
╔══════════════════════════════════════════════════════════════╗
║         🔍 SELECTOR FINDER v2.0 — Modo Estático            ║
║  Congela la página, bloquea ads/popups/animaciones y te     ║
║  da selectores CSS/XPath listos para Scrapy o Selenium.     ║
╚══════════════════════════════════════════════════════════════╝

Requisitos:
    pip install playwright
    playwright install chromium
"""

import asyncio
import json
from playwright.async_api import async_playwright

# ── Dominios de ads/trackers a bloquear ────────────────────────
AD_DOMAINS = {
    "doubleclick.net", "googlesyndication.com", "googleadservices.com",
    "google-analytics.com", "googletagmanager.com", "facebook.net",
    "facebook.com/tr", "fbcdn.net", "analytics.google.com",
    "adservice.google.com", "pagead2.googlesyndication.com",
    "amazon-adsystem.com", "ads.yahoo.com", "adskeeper.co.uk",
    "adnxs.com", "adsrvr.org", "adroll.com", "outbrain.com",
    "taboola.com", "criteo.com", "criteo.net", "moatads.com",
    "scorecardresearch.com", "quantserve.com", "zedo.com",
    "pubmatic.com", "openx.net", "rubiconproject.com",
    "bidswitch.net", "casalemedia.com", "sharethrough.com",
    "smartadserver.com", "advertising.com", "popads.net",
    "popcash.net", "propellerads.com", "mgid.com", "revcontent.com",
    "hotjar.com", "mixpanel.com", "segment.io", "segment.com",
    "optimizely.com", "crazyegg.com", "mouseflow.com",
    "fullstory.com", "clarity.ms", "newrelic.com", "sentry.io",
    "bugsnag.com", "rollbar.com", "tiktok.com/i18n",
    "snap.licdn.com", "ads.linkedin.com", "twitter.com/i/adsct",
    "t.co", "cdn.onesignal.com", "pushnami.com",
}

# ── Patrones de URL de ads ─────────────────────────────────────
AD_URL_PATTERNS = [
    "/ads/", "/ad/", "/adserver", "/adframe", "/adfetch",
    "pagead", "doubleclick", "googlesyndication",
    "/pop.js", "/popup.js", "/overlay.js",
    "push-notification", "onesignal", "pushnami",
    "/analytics.", "/tracker.", "/pixel.",
    "facebook.com/tr", "/fbevents",
]

# ── JS para congelar la página ─────────────────────────────────
FREEZE_JS = """
(() => {
    // ── 1. Matar todos los timers existentes ──
    const maxId = setTimeout(() => {}, 0);
    for (let i = 0; i < maxId; i++) {
        clearTimeout(i);
        clearInterval(i);
    }

    // ── 2. Bloquear nuevos timers (excepto los nuestros) ──
    const _origSetTimeout = window.setTimeout;
    const _origSetInterval = window.setInterval;
    window.__sfTimers = new Set();

    window.setTimeout = function(fn, delay, ...args) {
        const stack = new Error().stack || '';
        if (stack.includes('__selectorFinder')) {
            const id = _origSetTimeout.call(window, fn, delay, ...args);
            window.__sfTimers.add(id);
            return id;
        }
        return -1;
    };
    window.setInterval = function() { return -1; };

    // ── 3. Bloquear requestAnimationFrame ──
    window.requestAnimationFrame = function() { return -1; };
    window.cancelAnimationFrame = function() {};

    // ── 4. Congelar animaciones CSS ──
    const freezeStyle = document.createElement('style');
    freezeStyle.id = '__sf-freeze-style';
    freezeStyle.textContent = `
        *, *::before, *::after {
            animation-play-state: paused !important;
            animation: none !important;
            transition: none !important;
        }
    `;
    document.head.appendChild(freezeStyle);

    // ── 5. Cerrar popups / overlays / modales ──
    function killOverlays() {
        const selectors = [
            '[class*="popup"]', '[class*="Popup"]',
            '[class*="modal"]', '[class*="Modal"]',
            '[class*="overlay"]', '[class*="Overlay"]',
            '[class*="cookie"]', '[class*="Cookie"]',
            '[class*="consent"]', '[class*="Consent"]',
            '[class*="banner"]', '[class*="gdpr"]',
            '[class*="newsletter"]', '[class*="subscribe"]',
            '[class*="notification"]', '[class*="push"]',
            '[id*="popup"]', '[id*="modal"]',
            '[id*="overlay"]', '[id*="cookie"]',
            '[id*="consent"]', '[id*="gdpr"]',
            '[id*="newsletter"]', '[id*="onesignal"]',
        ];
        for (const sel of selectors) {
            document.querySelectorAll(sel).forEach(el => {
                const st = getComputedStyle(el);
                const isOverlay = (
                    (st.position === 'fixed' || st.position === 'absolute') &&
                    (parseInt(st.zIndex) > 100 || st.zIndex === 'auto')
                );
                if (isOverlay) el.remove();
            });
        }
        document.body.style.overflow = 'auto';
        document.documentElement.style.overflow = 'auto';
    }
    killOverlays();

    // ── 6. Eliminar iframes de ads ──
    document.querySelectorAll('iframe').forEach(iframe => {
        const src = (iframe.src || '').toLowerCase();
        const isAd = src.includes('ad') || src.includes('doubleclick') ||
                     src.includes('googlesyndication') || src.includes('facebook') ||
                     src.includes('taboola') || src.includes('outbrain') ||
                     iframe.width === '0' || iframe.height === '0' || !src;
        if (isAd) iframe.remove();
    });

    // ── 7. Eliminar scripts inline pendientes ──
    document.querySelectorAll('script:not([src])').forEach(s => s.remove());

    // ── 8. Bloquear MutationObservers nuevos ──
    window.MutationObserver = class {
        observe() {}
        disconnect() {}
        takeRecords() { return []; }
    };

    // ── 9. Bloquear WebSockets y EventSource ──
    window.WebSocket = class { close() {} send() {} };
    window.EventSource = class { close() {} };

    // ── 10. Bloquear service workers ──
    if (navigator.serviceWorker) {
        navigator.serviceWorker.register = () => Promise.reject('blocked');
    }

    // ── 11. Bloquear window.open (popups) ──
    window.open = () => null;

    // ── 12. Bloquear alert/confirm/prompt ──
    window.alert = () => {};
    window.confirm = () => false;
    window.prompt = () => null;

    // ── 13. Bloquear beforeunload ──
    window.onbeforeunload = null;
    window.addEventListener('beforeunload', e => e.stopImmediatePropagation(), true);

    console.log(JSON.stringify({type: '__sf_status__', msg: 'frozen'}));
})();
"""

# ── JavaScript del inspector de selectores ─────────────────────
INSPECTOR_JS = """
(() => {
    if (window.__selectorFinderActive) return;
    window.__selectorFinderActive = true;

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
            transition: none !important;
            animation: none !important;
        }
        #__sf-bar {
            position: fixed;
            top: 0; left: 0; right: 0;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%);
            color: #0f0;
            font-family: 'Consolas', 'Fira Code', monospace;
            font-size: 12px;
            padding: 6px 16px;
            z-index: 2147483647;
            pointer-events: none;
            border-bottom: 2px solid #2ecc71;
            display: flex;
            justify-content: space-between;
            transition: none !important;
            animation: none !important;
        }
    `;
    document.head.appendChild(style);

    // Barra superior informativa
    const bar = document.createElement('div');
    bar.id = '__sf-bar';
    bar.innerHTML = '<span>🔍 SELECTOR FINDER — Modo Estático</span><span>🧊 Página congelada • Ads bloqueados</span>';
    document.body.appendChild(bar);

    // Tooltip inferior
    const tooltip = document.createElement('div');
    tooltip.id = '__sf-tooltip';
    tooltip.textContent = '🖱️  Haz click en cualquier elemento para obtener su selector';
    document.body.appendChild(tooltip);

    // ── Generar selector CSS ──
    function getCssSelector(el) {
        if (el.id && !el.id.startsWith('__sf')) return `#${CSS.escape(el.id)}`;
        const parts = [];
        let current = el;
        while (current && current !== document.body && current !== document.documentElement) {
            let selector = current.tagName.toLowerCase();
            if (current.id && !current.id.startsWith('__sf')) {
                parts.unshift(`#${CSS.escape(current.id)}`);
                break;
            }
            const classes = Array.from(current.classList)
                .filter(c => !c.startsWith('__sf'))
                .map(c => `.${CSS.escape(c)}`);
            if (classes.length > 0) {
                selector += classes.slice(0, 3).join('');
                const test = [...(current.parentElement?.querySelectorAll(selector) || [])];
                if (test.length === 1) { parts.unshift(selector); break; }
            }
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
        if (el.id && !el.id.startsWith('__sf')) return `//*[@id="${el.id}"]`;
        const parts = [];
        let current = el;
        while (current && current.nodeType === Node.ELEMENT_NODE) {
            let tag = current.tagName.toLowerCase();
            if (current.id && !current.id.startsWith('__sf')) {
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

    // ── Atributos útiles ──
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
        const el = e.target;
        if (el.id?.startsWith('__sf')) return;
        if (lastHovered) lastHovered.classList.remove('__sf-hover');
        el.classList.add('__sf-hover');
        lastHovered = el;
        const tag = el.tagName.toLowerCase();
        const cls = Array.from(el.classList).filter(c => !c.startsWith('__sf')).join('.');
        tooltip.textContent = `🔍 <${tag}${cls ? '.' + cls : ''}> — click para inspeccionar`;
    }, true);

    document.addEventListener('mouseout', (e) => {
        e.target.classList.remove('__sf-hover');
    }, true);

    document.addEventListener('click', (e) => {
        if (e.target.id?.startsWith('__sf')) return;
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();

        const el = e.target;
        document.querySelectorAll('.__sf-selected').forEach(
            s => s.classList.remove('__sf-selected')
        );
        el.classList.add('__sf-selected');

        const css = getCssSelector(el);
        const xpath = getXPath(el);
        const text = (el.textContent || '').trim().slice(0, 100);
        const tag = el.tagName.toLowerCase();
        const attrs = getAttributes(el);

        const payload = JSON.stringify({
            type: '__selector_result__',
            tag, css, xpath,
            text: text || null,
            attributes: attrs
        });

        console.log(payload);
        tooltip.textContent = `✅ ${css}`;
    }, true);
})();
"""


# ── Colores terminal ──
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


def print_banner():
    print(f"""
{C.CYAN}{C.BOLD}╔══════════════════════════════════════════════════════════════╗
║         🔍  SELECTOR FINDER  v2.0 — Modo Estático          ║
║   🧊 Congela la página • 🚫 Bloquea ads • 🎯 Selectores   ║
╚══════════════════════════════════════════════════════════════╝{C.RESET}
""")


def print_selector_result(data: dict):
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

    blocked_count = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            permissions=[],
        )

        # Bloquear notificaciones push
        await context.grant_permissions([], origin=url)

        page = await context.new_page()

        # ── Interceptar TODAS las requests para bloquear ads ──
        async def handle_route(route):
            nonlocal blocked_count
            url_lower = route.request.url.lower()

            for domain in AD_DOMAINS:
                if domain in url_lower:
                    blocked_count += 1
                    await route.abort("blockedbyclient")
                    return

            for pattern in AD_URL_PATTERNS:
                if pattern in url_lower:
                    blocked_count += 1
                    await route.abort("blockedbyclient")
                    return

            resource = route.request.resource_type
            if resource in ("websocket", "eventsource", "manifest"):
                blocked_count += 1
                await route.abort("blockedbyclient")
                return

            await route.continue_()

        await page.route("**/*", handle_route)

        # ── Escuchar mensajes del JS inyectado ──
        def on_console(msg):
            text = msg.text
            if '__selector_result__' in text:
                try:
                    data = json.loads(text)
                    if data.get("type") == "__selector_result__":
                        print_selector_result(data)
                except json.JSONDecodeError:
                    pass
            elif '__sf_status__' in text:
                try:
                    data = json.loads(text)
                    if data.get("msg") == "frozen":
                        print(f"  {C.GREEN}🧊 Página congelada exitosamente.{C.RESET}")
                        print(f"  {C.GRAY}🚫 Requests bloqueados: {blocked_count}{C.RESET}")
                except json.JSONDecodeError:
                    pass

        page.on("console", on_console)

        try:
            print(f"  {C.YELLOW}⏳ Cargando: {url}{C.RESET}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            print(f"  {C.GREEN}✅ Página cargada.{C.RESET}")
        except Exception as e:
            print(f"  {C.RED}❌ Error al cargar: {e}{C.RESET}")
            await browser.close()
            return

        # ── Congelar la página ──
        print(f"  {C.YELLOW}🧊 Congelando página...{C.RESET}")
        await page.evaluate(FREEZE_JS)

        # Segunda pasada para overlays tardíos
        await asyncio.sleep(1)
        await page.evaluate("""
            document.querySelectorAll(
                '[class*="popup"], [class*="modal"], [class*="overlay"], ' +
                '[class*="cookie"], [class*="consent"], [class*="newsletter"]'
            ).forEach(el => {
                const st = getComputedStyle(el);
                if (st.position === 'fixed' || st.position === 'absolute') {
                    if (parseInt(st.zIndex) > 50) el.remove();
                }
            });
            document.querySelectorAll('iframe').forEach(f => {
                const src = (f.src || '').toLowerCase();
                if (!src || src.includes('ad') || src.includes('facebook') ||
                    src.includes('google')) f.remove();
            });
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
        """)

        # ── Inyectar el inspector ──
        await page.evaluate(INSPECTOR_JS)

        print(f"""
  {C.CYAN}{C.BOLD}┌──────────────────────────────────────────────────────┐
  │  🧊 Página CONGELADA — Modo estático activado       │
  │                                                      │
  │  ✅ Ads y trackers bloqueados ({blocked_count:>3} requests)         │
  │  ✅ Popups y modales eliminados                      │
  │  ✅ Animaciones y scripts pausados                   │
  │  ✅ WebSockets y notificaciones bloqueados           │
  │                                                      │
  │  🖱️  Haz click en cualquier elemento para ver       │
  │     su selector en la consola.                       │
  │                                                      │
  │  ❌ Cierra el navegador para terminar.               │
  └──────────────────────────────────────────────────────┘{C.RESET}
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
