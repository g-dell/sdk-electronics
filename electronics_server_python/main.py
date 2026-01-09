from __future__ import annotations

"""Electronics demo MCP server implemented with the Python FastMCP helper.

The server exposes widget-backed tools that render the Electronics UI bundle.
Each handler returns the HTML shell via an MCP resource and echoes structured
content so the ChatGPT client can hydrate the widget. The module also wires the
handlers into an HTTP/SSE stack so you can run the server with uvicorn on port
8000, matching the Node transport behavior.

Version: 1.0.0
MCP Protocol Version: 2024-11-05
"""

__version__ = "1.0.0"

import os
import logging
import duckdb
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Carica il file .env dalla root del progetto (non dalla directory electronics_server_python)
# __file__ è main.py in electronics_server_python/, quindi parent.parent è la root
# Prova anche nella directory corrente come fallback
env_paths = [
    Path(__file__).resolve().parent.parent / ".env",  # Root del progetto
    Path.cwd() / ".env",  # Directory corrente
    Path(__file__).resolve().parent / ".env",  # Directory electronics_server_python (fallback)
]

env_path = None
for path in env_paths:
    if path.exists():
        env_path = path
        load_dotenv(dotenv_path=env_path)
        break

if not env_path:
    # Prova comunque a caricare dalla directory corrente o dalle variabili d'ambiente di sistema
    load_dotenv()

# Configurazione logging per activity logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Log info sul caricamento del file .env (dopo che logger è stato configurato)
if env_path:
    logger.info(f"Loaded .env file from: {env_path}")
    # Verifica se MOTHERDUCK_TOKEN è presente dopo il caricamento
    token_after_load = os.getenv("MOTHERDUCK_TOKEN")
    if token_after_load:
        logger.info("MOTHERDUCK_TOKEN found in .env file")
    else:
        logger.warning("MOTHERDUCK_TOKEN not found in .env file after loading. Check that it exists in the file.")
else:
    logger.warning(f".env file not found in any of the searched paths. Environment variables will be read from system environment.")
    logger.warning(f"Searched paths: {env_paths}")

from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import mcp.types as types
import uvicorn
from fastapi import Request, FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from mcp.server.fastmcp import FastMCP
from starlette.staticfiles import StaticFiles
from starlette.routing import Mount, Route
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse as StarletteHTMLResponse, Response
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import BaseModel, ConfigDict, Field, ValidationError
import httpx
from urllib.parse import urlparse, urlencode


@dataclass(frozen=True)
class ElectronicsWidget:
    identifier: str
    title: str
    template_uri: str
    invoking: str
    invoked: str
    html: str
    response_text: str


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

def get_motherduck_connection():
    """
    Crea e restituisce una connessione DuckDB al database MotherDuck.
    
    Returns:
        duckdb.DuckDBPyConnection: Connessione al database MotherDuck.
        
    Raises:
        ValueError: Se MOTHERDUCK_TOKEN non è configurato come variabile d'ambiente.
    """
    md_token = os.getenv("MOTHERDUCK_TOKEN")
    if not md_token:
        raise ValueError(
            "MOTHERDUCK_TOKEN non trovato nelle variabili d'ambiente. "
            "Configurare MOTHERDUCK_TOKEN per connettersi a MotherDuck."
        )
    
    # Connessione a MotherDuck usando il formato md:database_name?motherduck_token=TOKEN
    # Il database è 'app_gpt_elettronica'
    connection_string = f"md:app_gpt_elettronica?motherduck_token={md_token}"
    con = duckdb.connect(connection_string)
    
    # Imposta lo schema di ricerca su 'main' per semplificare le query
    con.execute("SET search_path TO main;")
    
    return con


async def get_products_from_motherduck():
    """
    Recupera i prodotti elettronici dal database MotherDuck.
    
    Returns:
        List[Dict[str, Any]]: Lista di prodotti come dizionari Python.
        Ritorna lista vuota in caso di errore.
    """
    try:
        logger.info("Connecting to MotherDuck database")
        with get_motherduck_connection() as con:
            # Query per recuperare tutti i prodotti dalla tabella prodotti_xeel_shop
            # La tabella è nello schema 'main' (impostato in get_motherduck_connection)
            query = "SELECT * FROM prodotti_xeel_shop"
            logger.debug(f"Executing query: {query}")
            products_df = con.execute(query).fetchdf()
            
            # Converti DataFrame in lista di dizionari per compatibilità JSON
            products = products_df.to_dict(orient="records")
            
            # Log per audit
            if products:
                logger.info(f"Retrieved {len(products)} products from MotherDuck")
            else:
                logger.warning("No products retrieved from MotherDuck (empty result)")
            
            return products
    except ValueError as e:
        # Errore di configurazione (es. MOTHERDUCK_TOKEN mancante)
        logger.warning(
            f"MotherDuck token not configured: {e}. "
            "Widgets will display empty data until MOTHERDUCK_TOKEN is configured."
        )
        return []
    except Exception as e:
        # Altri errori (es. connessione, query, ecc.)
        logger.error(f"Error retrieving products from MotherDuck: {e}", exc_info=True)
        return []


def transform_products_to_places(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Trasforma prodotti dal database MotherDuck in formato 'places' per i widget UI.
    
    I widget carousel/map/list/albums si aspettano una struttura 'places' con:
    - id, name, coords (lat, lon), description, city, rating, price (stringa), thumbnail
    
    I prodotti dal database prodotti_xeel_shop hanno:
    - id, name, prices.amountMax/prices.amountMin, descrizione_prodotto, imageURLs, 
      voto_prodotto_1_5, categories, primaryCategories
    
    Questa funzione mappa i campi dal database e genera valori default per campi mancanti 
    (coords, city - generati automaticamente).
    
    Mapping colonne DB -> places:
    - id -> id
    - name -> name  
    - prices.amountMax -> price (convertito in $/$$/$$$)
    - descrizione_prodotto -> description
    - imageURLs -> thumbnail
    - voto_prodotto_1_5 -> rating (con fallback a 4.5)
    - coords, city -> generati automaticamente (default San Francisco)
    
    Args:
        products: Lista di prodotti dal database (dizionari Python)
    
    Returns:
        Lista di 'places' nel formato atteso dai widget
    """
    if not products:
        return []
    
    # Coordinate di default per San Francisco (dove sono i place attuali in markers.json)
    # Distribuite in diverse zone della città per varietà visiva
    default_coords = [
        [-122.4098, 37.8001],  # North Beach
        [-122.4093, 37.7990],  # North Beach
        [-122.4255, 37.7613],  # Mission
        [-122.4388, 37.7775],  # Alamo Square
        [-122.4077, 37.7990],  # North Beach
        [-122.4097, 37.7992],  # North Beach
        [-122.4380, 37.7722],  # Lower Haight
        [-122.4123, 37.7899],  # Nob Hill
        [-122.4135, 37.7805],  # SoMa
        [-122.4019, 37.7818],  # Yerba Buena
        [-122.4194, 37.7749],  # Mission
        [-122.4313, 37.7849],  # Western Addition
    ]
    
    # Città di default
    default_cities = [
        "San Francisco",
        "North Beach",
        "Mission",
        "Alamo Square",
        "SoMa",
        "Nob Hill",
        "Lower Haight",
        "Yerba Buena",
    ]
    
    places = []
    for idx, product in enumerate(products):
        # Ottieni il prezzo da prices.amountMax (colonna nel DB con dot notation)
        # DuckDB restituisce le colonne con dot come chiavi con dot o come dict annidato
        price_num = 0
        if "prices.amountMax" in product:
            price_num = product.get("prices.amountMax", 0)
        elif isinstance(product.get("prices"), dict):
            price_num = product.get("prices", {}).get("amountMax", 0)
        
        # Converti prezzo in formato stringa ($, $$, $$$)
        if isinstance(price_num, (int, float)) and price_num > 0:
            if price_num < 50:
                price_str = "$"
            elif price_num < 100:
                price_str = "$$"
            else:
                price_str = "$$$"
        else:
            price_str = "$$"  # Default
        
        # Genera coordinate usando pattern circolare sulle coordinate default
        coords = default_coords[idx % len(default_coords)]
        
        # Genera città usando pattern circolare
        city = default_cities[idx % len(default_cities)]
        
        # Rating dal database (voto_prodotto_1_5) o default
        rating = product.get("voto_prodotto_1_5", 4.5)
        if not isinstance(rating, (int, float)) or rating <= 0:
            rating = 4.5  # Default se non valido
        
        # Mappa i campi usando i nomi colonne corretti del database
        place = {
            "id": product.get("id", f"product-{idx}"),
            "name": product.get("name", "Unknown Product"),
            "coords": coords,
            "description": product.get("descrizione_prodotto", ""),  # Usa descrizione_prodotto dal DB
            "city": city,
            "rating": rating,
            "price": price_str,
            "thumbnail": product.get("imageURLs", ""),  # Usa solo imageURLs (non esiste "image" nel DB)
        }
        
        # Assicurati che thumbnail sia una stringa (se imageURLs è una lista, prendi il primo)
        if isinstance(place["thumbnail"], list):
            place["thumbnail"] = place["thumbnail"][0] if place["thumbnail"] else ""
        elif not place["thumbnail"]:
            place["thumbnail"] = ""
        
        places.append(place)
    
    return places


def transform_products_to_albums(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Trasforma prodotti dal database MotherDuck in formato 'albums' per il widget albums.
    
    Il widget albums si aspetta una struttura con:
    - albums array
      - id, title, cover
      - photos array con id, title, url
    
    Strategia: Raggruppa prodotti per categoria (primaryCategories o categories).
    I prodotti dal database prodotti_xeel_shop hanno:
    - primaryCategories (colonna preferita) o categories (fallback)
    - imageURLs per le immagini
    - name per il titolo
    
    Args:
        products: Lista di prodotti dal database (dizionari Python)
    
    Returns:
        Lista di 'albums' nel formato atteso dal widget albums
    """
    if not products:
        return []
    
    # Raggruppa prodotti per tag principale (primo tag più comune)
    # Oppure crea album tematici
    albums_map = {}
    
    for product in products:
        # Usa primaryCategories o categories dal database (non esiste "tags")
        categories = []
        if product.get("primaryCategories"):
            if isinstance(product["primaryCategories"], list):
                categories = product["primaryCategories"]
            elif isinstance(product["primaryCategories"], str):
                categories = [cat.strip() for cat in product["primaryCategories"].split(",")]
        elif product.get("categories"):
            if isinstance(product["categories"], list):
                categories = product["categories"]
            elif isinstance(product["categories"], str):
                categories = [cat.strip() for cat in product["categories"].split(",")]
        
        # Usa la prima categoria come categoria principale, o "General" se non ci sono
        category = categories[0] if categories else "General Electronics"
        
        # Normalizza il nome della categoria per l'id dell'album
        album_id = category.lower().replace(" ", "-").replace("&", "and")[:30]
        
        if album_id not in albums_map:
            albums_map[album_id] = {
                "id": album_id,
                "title": category,
                "cover": product.get("imageURLs", "") or "",  # Usa solo imageURLs (non esiste "image" nel DB)
                "photos": [],
            }
            
            # Assicurati che cover sia una stringa
            if isinstance(albums_map[album_id]["cover"], list):
                albums_map[album_id]["cover"] = albums_map[album_id]["cover"][0] if albums_map[album_id]["cover"] else ""
        
        # Aggiungi prodotto come photo nell'album
        photo = {
            "id": product.get("id", f"photo-{len(albums_map[album_id]['photos'])}"),
            "title": product.get("name", "Product"),
            "url": product.get("imageURLs", "") or "",  # Usa solo imageURLs (non esiste "image" nel DB)
        }
        
        # Assicurati che url sia una stringa
        if isinstance(photo["url"], list):
            photo["url"] = photo["url"][0] if photo["url"] else ""
        
        albums_map[album_id]["photos"].append(photo)
    
    # Se non ci sono album creati (nessun tag), crea un album unico con tutti i prodotti
    if not albums_map:
        albums_map["all-products"] = {
            "id": "all-products",
            "title": "All Products",
            "cover": products[0].get("image") or products[0].get("imageURLs", "") if products else "",
            "photos": [],
        }
        
        if isinstance(albums_map["all-products"]["cover"], list):
            albums_map["all-products"]["cover"] = albums_map["all-products"]["cover"][0] if albums_map["all-products"]["cover"] else ""
        
        for product in products:
            photo = {
                "id": product.get("id", f"photo-{len(albums_map['all-products']['photos'])}"),
                "title": product.get("name", "Product"),
                "url": product.get("image") or product.get("imageURLs", "") or "",
            }
            if isinstance(photo["url"], list):
                photo["url"] = photo["url"][0] if photo["url"] else ""
            albums_map["all-products"]["photos"].append(photo)
    
    # Converti dict in lista e limita a massimo 4 album
    albums = list(albums_map.values())[:4]
    
    return albums


@lru_cache(maxsize=None)
def _load_widget_html(component_name: str) -> str:
    html_path = ASSETS_DIR / f"{component_name}.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf8")

    fallback_candidates = sorted(ASSETS_DIR.glob(f"{component_name}-*.html"))
    if fallback_candidates:
        return fallback_candidates[-1].read_text(encoding="utf8")

    raise FileNotFoundError(
        f'Widget HTML for "{component_name}" not found in {ASSETS_DIR}. '
        "Run `pnpm run build` to generate the assets before starting the server."
    )


widgets: List[ElectronicsWidget] = [
    ElectronicsWidget(
        identifier="electronics-map",
        title="Show Electronics Map",
        template_uri="ui://widget/electronics-map.html",
        invoking="Loading electronics map",
        invoked="Electronics map loaded",
        html=_load_widget_html("electronics"),
        response_text="Rendered an electronics map!",
    ),
    ElectronicsWidget(
        identifier="electronics-carousel",
        title="Show Electronics Carousel",
        template_uri="ui://widget/electronics-carousel.html",
        invoking="Loading electronics carousel",
        invoked="Electronics carousel loaded",
        html=_load_widget_html("electronics-carousel"),
        response_text="Rendered an electronics carousel!",
    ),
    ElectronicsWidget(
        identifier="electronics-albums",
        title="Show Electronics Album",
        template_uri="ui://widget/electronics-albums.html",
        invoking="Loading electronics album",
        invoked="Electronics album loaded",
        html=_load_widget_html("electronics-albums"),
        response_text="Rendered an electronics album!",
    ),
    ElectronicsWidget(
        identifier="electronics-list",
        title="Show Electronics List",
        template_uri="ui://widget/electronics-list.html",
        invoking="Loading electronics list",
        invoked="Electronics list loaded",
        html=_load_widget_html("electronics-list"),
        response_text="Rendered an electronics list!",
    ),
    ElectronicsWidget(
        identifier="electronics-shop",
        title="Open Electronics Shop",
        template_uri="ui://widget/electronics-shop.html",
        invoking="Opening the electronics shop",
        invoked="Electronics shop opened",
        html=_load_widget_html("electronics-shop"),
        response_text="Rendered the Electronics shop!",
    ),
    ElectronicsWidget(
        identifier="product-list",
        title="List Products from MotherDuck",
        template_uri="ui://widget/product-list.html",
        invoking="Fetching products",
        invoked="Fetched products from MotherDuck",
        html="<p>Product list is being rendered...</p>",
        response_text="Here are the products from MotherDuck!",
    ),
]

MIME_TYPE = "text/html+skybridge"


WIDGETS_BY_ID: Dict[str, ElectronicsWidget] = {
    widget.identifier: widget for widget in widgets
}
WIDGETS_BY_URI: Dict[str, ElectronicsWidget] = {
    widget.template_uri: widget for widget in widgets
}


# Note: ElectronicsInput removed - most widgets don't require input parameters
# If needed in the future, create ElectronicsInput with appropriate fields


def _split_env_list(value: str | None) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _transport_security_settings() -> TransportSecuritySettings:
    allowed_hosts = _split_env_list(os.getenv("MCP_ALLOWED_HOSTS"))
    allowed_origins = _split_env_list(os.getenv("MCP_ALLOWED_ORIGINS"))
    if not allowed_hosts and not allowed_origins:
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


class CORSMiddleware(BaseHTTPMiddleware):
    """
    Middleware per aggiungere CORS (Cross-Origin Resource Sharing) headers alle risposte HTTP.
    
    Permette al browser di caricare risorse (JS, CSS) da origini diverse, necessario
    quando il widget viene caricato da ChatGPT che ha un'origine diversa dal server.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Gestisci richieste OPTIONS (preflight) prima di chiamare il prossimo middleware
        if request.method == "OPTIONS":
            origin = request.headers.get("origin")
            allowed_origins = _split_env_list(os.getenv("MCP_ALLOWED_ORIGINS"))
            
            response = Response(status_code=200)
            
            # Imposta Access-Control-Allow-Origin
            if not allowed_origins:
                # Permetti tutte le origini (utile per sviluppo e per ChatGPT)
                response.headers["Access-Control-Allow-Origin"] = "*"
            elif origin and origin in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
            elif origin:
                # Se l'origine non è nella lista ma è presente, la permettiamo comunque
                # (utile per ChatGPT che può avere origini dinamiche)
                response.headers["Access-Control-Allow-Origin"] = origin
            
            # Header necessari per CORS
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Max-Age"] = "86400"  # 24 ore
            
            return response
        
        # Per risposte SSE (/mcp endpoint), passa direttamente senza modificare headers
        # Le risposte SSE sono gestite direttamente da sse-starlette e non seguono il normale flusso HTTP
        if request.url.path.startswith("/mcp") or request.url.path == "/sse":
            return await call_next(request)
        
        # Per tutte le altre richieste, processa normalmente e aggiungi header CORS
        response = await call_next(request)
        
        # Ottieni l'origine della richiesta
        origin = request.headers.get("origin")
        
        # Lista di origini permesse (può essere configurata via env)
        allowed_origins = _split_env_list(os.getenv("MCP_ALLOWED_ORIGINS"))
        
        # Imposta Access-Control-Allow-Origin
        if not allowed_origins:
            # Permetti tutte le origini (utile per sviluppo e per ChatGPT)
            response.headers["Access-Control-Allow-Origin"] = "*"
        elif origin and origin in allowed_origins:
            # Permetti solo origini specificate
            response.headers["Access-Control-Allow-Origin"] = origin
        elif origin:
            # Se l'origine non è nella lista ma è presente, la permettiamo comunque
            # (utile per ChatGPT che può avere origini dinamiche)
            response.headers["Access-Control-Allow-Origin"] = origin
        
        # Header necessari per CORS
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        return response


class CSPMiddleware(BaseHTTPMiddleware):
    """
    Middleware per aggiungere Content Security Policy (CSP) headers alle risposte HTTP.
    
    CSP previene attacchi XSS limitando le risorse che possono essere caricate ed eseguite.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Per risposte SSE (/mcp endpoint), passa direttamente senza modificare headers
        # Le risposte SSE sono gestite direttamente da sse-starlette e non seguono il normale flusso HTTP
        if request.url.path.startswith("/mcp") or request.url.path == "/sse":
            return await call_next(request)
        
        response = await call_next(request)
        
        # Costruisci la policy CSP come stringa singola per evitare problemi con h11
        # h11 (usato da uvicorn) è molto rigoroso nella validazione degli header HTTP
        csp_policy = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://chat.openai.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        
        # Aggiungi header CSP alla risposta
        # Nota: se h11 continua a rifiutare l'header, potrebbe essere necessario
        # rimuovere temporaneamente il middleware CSP o usare un approccio alternativo
        try:
            response.headers["Content-Security-Policy"] = csp_policy
        except Exception as e:
            # Se h11 rifiuta l'header, loggiamo l'errore ma non blocchiamo la risposta
            # Questo permette al server di funzionare anche senza CSP
            logger.warning(f"Failed to set CSP header: {e}")
        
        # Aggiungi anche header X-Content-Type-Options per sicurezza aggiuntiva
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Aggiungi header X-Frame-Options per prevenire clickjacking (redundante con CSP frame-ancestors ma utile per browser vecchi)
        response.headers["X-Frame-Options"] = "DENY"
        
        return response


async def proxy_image_handler(request: Request):
    """
    Proxy endpoint per servire immagini esterne con header CORS corretti.
    
    Risolve il problema ERR_BLOCKED_BY_ORB (Opaque Response Blocking) che si verifica
    quando il browser blocca immagini cross-origin senza header CORS appropriati.
    
    Query parameters:
        url (required): URL dell'immagine da proxyare (deve essere URL-encoded)
    
    Returns:
        Response con l'immagine e header CORS corretti, oppure errore 400/500
    """
    # Estrai l'URL dell'immagine dai query parameters
    image_url = request.query_params.get("url")
    
    if not image_url:
        logger.warning("Proxy image request without 'url' parameter")
        return Response(
            content="Missing 'url' parameter",
            status_code=400,
            media_type="text/plain"
        )
    
    # Valida che sia un URL valido
    try:
        parsed_url = urlparse(image_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL format")
        
        # Whitelist di domini permessi (opzionale, per sicurezza)
        # Per ora permettiamo tutti i domini, ma si può restringere se necessario
        allowed_domains = os.getenv("PROXY_ALLOWED_DOMAINS", "").split(",")
        if allowed_domains and allowed_domains[0]:  # Se configurato
            domain = parsed_url.netloc.lower()
            if not any(allowed in domain for allowed in allowed_domains if allowed):
                logger.warning(f"Proxy request blocked for domain: {domain}")
                return Response(
                    content="Domain not allowed",
                    status_code=403,
                    media_type="text/plain"
                )
    except Exception as e:
        logger.warning(f"Invalid URL in proxy request: {image_url}, error: {e}")
        return Response(
            content=f"Invalid URL: {str(e)}",
            status_code=400,
            media_type="text/plain"
        )
    
    try:
        # Scarica l'immagine dal server esterno
        logger.debug(f"Proxying image from: {image_url}")
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            image_response = await client.get(image_url)
            image_response.raise_for_status()  # Solleva eccezione se status non è 2xx
        
        # Determina il content type dall'header o dall'estensione
        content_type = image_response.headers.get("content-type", "image/png")
        if not content_type.startswith("image/"):
            # Se il content-type non è un'immagine, prova a dedurlo dall'URL
            ext = parsed_url.path.lower().split(".")[-1] if "." in parsed_url.path else ""
            content_type_map = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "gif": "image/gif",
                "webp": "image/webp",
                "svg": "image/svg+xml",
            }
            content_type = content_type_map.get(ext, "image/png")
        
        # Crea la risposta con l'immagine e header CORS
        response = Response(
            content=image_response.content,
            status_code=200,
            media_type=content_type
        )
        
        # Aggiungi header CORS per permettere il caricamento cross-origin
        origin = request.headers.get("origin")
        allowed_origins = _split_env_list(os.getenv("MCP_ALLOWED_ORIGINS"))
        
        if not allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        elif origin and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
        elif origin:
            # Permetti l'origine se presente (utile per ChatGPT con origini dinamiche)
            response.headers["Access-Control-Allow-Origin"] = origin
        
        # Header aggiuntivi per caching e sicurezza
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Cache-Control"] = "public, max-age=86400"  # Cache per 24 ore
        
        # Copia header utili dall'immagine originale (se presenti)
        if "etag" in image_response.headers:
            response.headers["ETag"] = image_response.headers["etag"]
        if "last-modified" in image_response.headers:
            response.headers["Last-Modified"] = image_response.headers["last-modified"]
        
        logger.debug(f"Successfully proxied image: {image_url} ({len(image_response.content)} bytes)")
        return response
        
    except httpx.TimeoutException:
        logger.error(f"Timeout while proxying image: {image_url}")
        return Response(
            content="Timeout while fetching image",
            status_code=504,
            media_type="text/plain"
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error while proxying image: {image_url}, status: {e.response.status_code}")
        return Response(
            content=f"Failed to fetch image: HTTP {e.response.status_code}",
            status_code=e.response.status_code,
            media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"Error proxying image: {image_url}, error: {str(e)}", exc_info=True)
        return Response(
            content=f"Error proxying image: {str(e)}",
            status_code=500,
            media_type="text/plain"
        )


# Handler per richieste OPTIONS (preflight) per il proxy
async def proxy_image_options_handler(request: Request):
    """Handler per richieste OPTIONS (preflight) per il proxy immagini."""
    origin = request.headers.get("origin")
    allowed_origins = _split_env_list(os.getenv("MCP_ALLOWED_ORIGINS"))
    
    response = Response(status_code=200)
    
    if not allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = "*"
    elif origin and origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
    elif origin:
        response.headers["Access-Control-Allow-Origin"] = origin
    
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Max-Age"] = "86400"
    
    return response


mcp = FastMCP(
    name="electronics-python",
    stateless_http=True,
    transport_security=_transport_security_settings(),
)

# Aggiungi middleware CSP all'app FastAPI
# Nota: FastMCP espone l'app tramite sse_app(), quindi dobbiamo aggiungere il middleware
# dopo che l'app è creata, ma prima di esporla


# Tool input schemas - most widgets don't require input
# Define specific schemas per tool if needed
EMPTY_TOOL_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {},
    "required": [],
    "additionalProperties": False,
}



def _resource_description(widget: ElectronicsWidget) -> str:
    return f"{widget.title} widget markup"


def _tool_description(widget: ElectronicsWidget) -> str:
    """
    Genera una descrizione dettagliata per ogni tool basata sul suo identificatore.
    
    Returns:
        str: Descrizione dettagliata del tool che spiega cosa fa, quando usarlo e cosa restituisce.
    """
    descriptions = {
        "electronics-map": (
            "Mostra una mappa interattiva dei negozi di elettronica. "
            "Usa questo tool quando l'utente chiede di vedere la posizione dei negozi o di visualizzare "
            "una mappa interattiva. Restituisce un widget HTML con una mappa cliccabile."
        ),
        "electronics-carousel": (
            "Mostra un carosello interattivo di prodotti elettronici. "
            "Usa questo tool quando l'utente vuole sfogliare prodotti in formato carosello o visualizzare "
            "una selezione di prodotti in modo interattivo. Restituisce un widget HTML con un carosello navigabile."
        ),
        "electronics-albums": (
            "Mostra una galleria di prodotti elettronici con visualizzazione a album. "
            "Usa questo tool quando l'utente chiede di vedere una galleria di prodotti, foto o immagini "
            "in formato album. Restituisce un widget HTML con una galleria interattiva."
        ),
        "electronics-list": (
            "Mostra una lista di prodotti elettronici. "
            "Usa questo tool quando l'utente chiede di vedere un elenco di prodotti o una lista semplice. "
            "Restituisce un widget HTML con una lista formattata di prodotti."
        ),
        "electronics-shop": (
            "Apre il negozio elettronico completo con funzionalità di shopping. "
            "Usa questo tool quando l'utente vuole accedere al negozio completo, vedere prodotti con dettagli, "
            "o iniziare lo shopping. Restituisce un widget HTML con l'interfaccia completa del negozio."
        ),
        "product-list": (
            "Recupera e mostra la lista completa di prodotti elettronici dal database MotherDuck. "
            "Usa questo tool quando l'utente chiede di vedere tutti i prodotti disponibili, cercare prodotti, "
            "o visualizzare il catalogo completo. Restituisce un widget HTML con i prodotti recuperati dal database, "
            "inclusi dettagli come nome, prezzo, descrizione e immagini."
        ),
    }
    return descriptions.get(widget.identifier, widget.title)


def _tool_meta(widget: ElectronicsWidget) -> Dict[str, Any]:
    return {
        "openai/outputTemplate": widget.template_uri,
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
        "openai/widgetAccessible": True,
    }


def _tool_invocation_meta(widget: ElectronicsWidget) -> Dict[str, Any]:
    return {
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
    }



@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    """
    Lista tutti i tool disponibili nel server MCP.
    
    Returns:
        List[types.Tool]: Lista di tool con schemi input, descrizioni dettagliate e metadati.
    """
    return [
        types.Tool(
            name=widget.identifier,
            title=widget.title,
            description=_tool_description(widget),
            inputSchema=deepcopy(EMPTY_TOOL_INPUT_SCHEMA),
            _meta=_tool_meta(widget),
            # Annotazioni per indicare che i tool sono read-only e non distruttivi
            annotations={
                "destructiveHint": False,  # I tool non modificano dati
                "openWorldHint": False,    # I tool non accedono a dati esterni non controllati
                "readOnlyHint": True,      # I tool sono read-only
            },
        )
        for widget in widgets
    ]


@mcp._mcp_server.list_resources()
async def _list_resources() -> List[types.Resource]:
    return [
        types.Resource(
            name=widget.title,
            title=widget.title,
            uri=widget.template_uri,
            description=_resource_description(widget),
            mimeType=MIME_TYPE,
            _meta=_tool_meta(widget),
        )
        for widget in widgets
    ]


@mcp._mcp_server.list_resource_templates()
async def _list_resource_templates() -> List[types.ResourceTemplate]:
    return [
        types.ResourceTemplate(
            name=widget.title,
            title=widget.title,
            uriTemplate=widget.template_uri,
            description=_resource_description(widget),
            mimeType=MIME_TYPE,
            _meta=_tool_meta(widget),
        )
        for widget in widgets
    ]


async def _handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    widget = WIDGETS_BY_URI.get(str(req.params.uri))
    if widget is None:
        return types.ServerResult(
            types.ReadResourceResult(
                contents=[],
                _meta={"error": f"Unknown resource: {req.params.uri}"},
            )
        )

    # Rewrite HTML to use correct paths for JS/CSS files
    # Handles multiple cases:
    # - http://localhost:4444/file.js -> /assets/file.js or BASE_URL/assets/file.js
    # - http://localhost:4444/assets/file.js -> /assets/file.js or BASE_URL/assets/file.js
    # - /file.js -> /assets/file.js or BASE_URL/assets/file.js
    html_content = widget.html
    import re
    
    base_url = os.getenv("BASE_URL", "").rstrip("/")
    
    def fix_asset_path(match):
        attr, path = match.group(1), match.group(2)
        # Remove leading slash if present, ensure assets/ prefix
        path = path.lstrip('/')
        if not path.startswith('assets/'):
            path = f'assets/{path}'
        
        if base_url:
            return f'{attr}="{base_url}/{path}"'
        else:
            return f'{attr}="/{path}"'
    
    # Pattern 1: localhost URLs (with or without assets/)
    html_content = re.sub(
        r'(src|href)="http://localhost:\d+/([^"]+\.(js|css))"',
        fix_asset_path,
        html_content
    )
    
    # Pattern 2: Absolute root paths
    html_content = re.sub(
        r'(src|href)="/([^"]+\.(js|css))"',
        fix_asset_path,
        html_content
    )
    
    # Pattern 3: BASE_URL paths (if set)
    if base_url:
        html_content = re.sub(
            rf'(src|href)="{re.escape(base_url)}/(?!assets/)([^"]+\.(js|css))"',
            fix_asset_path,
            html_content
        )

    # Inject server base URL for proxy configuration
    # This allows the frontend to know the server URL for proxy requests
    # Use BASE_URL from environment if available, otherwise use empty string (relative URLs)
    server_url = base_url or ""
    
    # Inject script to set server URL before closing </head> or before </body>
    injection_script = f"""<script>
    // Inject server base URL for image proxy configuration
    if (typeof window !== 'undefined') {{
      window.__ELECTRONICS_SERVER_URL__ = {repr(server_url)};
      console.log('[Server] Injected server base URL:', window.__ELECTRONICS_SERVER_URL__);
    }}
    </script>"""
    
    # Try to inject before </head>, if not found inject before </body>
    if "</head>" in html_content:
        html_content = html_content.replace("</head>", injection_script + "\n</head>", 1)
    elif "</body>" in html_content:
        html_content = html_content.replace("</body>", injection_script + "\n</body>", 1)
    else:
        # If no head or body tag, prepend to HTML
        html_content = injection_script + "\n" + html_content

    contents = [
        types.TextResourceContents(
            uri=widget.template_uri,
            mimeType=MIME_TYPE,
            text=html_content,
            _meta=_tool_meta(widget),
        )
    ]

    return types.ServerResult(types.ReadResourceResult(contents=contents))


async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    """
    Gestisce le richieste di esecuzione tool con logging per audit.
    
    Logs:
    - Tool name e arguments (senza dati sensibili)
    - Timestamp dell'esecuzione
    - Successo/errore dell'esecuzione
    - Durata dell'esecuzione (se possibile)
    """
    tool_name = req.params.name
    arguments = req.params.arguments or {}
    start_time = datetime.now()
    
    # Log inizio esecuzione tool (senza dati sensibili)
    logger.info(
        f"Tool execution started: tool={tool_name}, "
        f"arguments_keys={list(arguments.keys()) if arguments else 'none'}"
    )
    
    widget = WIDGETS_BY_ID.get(tool_name)
    if widget is None:
        error_msg = f"Unknown tool: {tool_name}"
        logger.warning(f"Tool execution failed: tool={tool_name}, error={error_msg}")
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=error_msg,
                    )
                ],
                isError=True,
            )
        )

    try:
        if tool_name == "product-list":
            # Tool che richiede accesso a MotherDuck
            logger.info(f"Tool {tool_name}: Fetching products from MotherDuck")
            products = await get_products_from_motherduck()
            product_count = len(products) if products else 0
            if product_count == 0:
                # Se la lista è vuota, potrebbe essere dovuto a:
                # 1. Errore precedente (pandas mancante, token mancante, ecc.) - già loggato come ERROR/WARNING
                # 2. Database vuoto - comportamento normale
                logger.warning(
                    f"Tool {tool_name}: No products retrieved from MotherDuck. "
                    "Widget will display empty products list. "
                    "Check previous logs for errors (e.g., pandas missing, MOTHERDUCK_TOKEN not configured, or database connection issues)."
                )
            else:
                logger.info(f"Tool {tool_name}: Retrieved {product_count} products from MotherDuck")
            
            result = types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text=widget.response_text,
                        )
                    ],
                    structuredContent={"products": products},
                    _meta=_tool_invocation_meta(widget),
                )
            )
        elif tool_name == "electronics-albums":
            # Widget che usa formato 'albums' - recupera prodotti e trasforma in albums
            logger.info(f"Tool {tool_name}: Fetching products from MotherDuck and transforming to albums")
            products = await get_products_from_motherduck()
            albums = transform_products_to_albums(products)
            album_count = len(albums) if albums else 0
            if album_count == 0:
                # Se la lista è vuota, potrebbe essere dovuto a:
                # 1. Errore precedente (pandas mancante, token mancante, ecc.) - già loggato come ERROR/WARNING
                # 2. Database vuoto - comportamento normale
                logger.warning(
                    f"Tool {tool_name}: No products retrieved from MotherDuck. "
                    "Widget will display empty albums list. "
                    "Check previous logs for errors (e.g., pandas missing, MOTHERDUCK_TOKEN not configured, or database connection issues)."
                )
            else:
                logger.info(f"Tool {tool_name}: Retrieved {len(products)} products, transformed to {album_count} albums")
            
            # Valida che non ci siano argomenti inattesi
            if arguments:
                logger.warning(
                    f"Tool {tool_name}: Received unexpected arguments: {list(arguments.keys())}. "
                    "Ignoring arguments as this tool does not require input."
                )
            
            result = types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text=widget.response_text,
                        )
                    ],
                    structuredContent={"albums": albums},
                    _meta=_tool_invocation_meta(widget),
                )
            )
        elif tool_name in ["electronics-carousel", "electronics-map", "electronics-list", "mixed-auth-search"]:
            # Widget che usano formato 'places' - recupera prodotti e trasforma in places
            logger.info(f"Tool {tool_name}: Fetching products from MotherDuck and transforming to places")
            products = await get_products_from_motherduck()
            places = transform_products_to_places(products)
            place_count = len(places) if places else 0
            if place_count == 0:
                # Se la lista è vuota, potrebbe essere dovuto a:
                # 1. Errore precedente (pandas mancante, token mancante, ecc.) - già loggato come ERROR/WARNING
                # 2. Database vuoto - comportamento normale
                logger.warning(
                    f"Tool {tool_name}: No products retrieved from MotherDuck. "
                    "Widget will display empty places list. "
                    "Check previous logs for errors (e.g., pandas missing, MOTHERDUCK_TOKEN not configured, or database connection issues)."
                )
            else:
                logger.info(f"Tool {tool_name}: Retrieved {len(products)} products, transformed to {place_count} places")
            
            # Valida che non ci siano argomenti inattesi
            if arguments:
                logger.warning(
                    f"Tool {tool_name}: Received unexpected arguments: {list(arguments.keys())}. "
                    "Ignoring arguments as this tool does not require input."
                )
            
            result = types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text=widget.response_text,
                        )
                    ],
                    structuredContent={"places": places},
                    _meta=_tool_invocation_meta(widget),
                )
            )
        else:
            # Widget di visualizzazione che non richiedono input e non usano database
            # Valida che non ci siano argomenti inattesi
            if arguments:
                logger.warning(
                    f"Tool {tool_name}: Received unexpected arguments: {list(arguments.keys())}. "
                    "Ignoring arguments as this tool does not require input."
                )
            
            result = types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text=widget.response_text,
                        )
                    ],
                    structuredContent={},
                    _meta=_tool_invocation_meta(widget),
                )
            )
        
        # Log successo esecuzione
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Tool execution completed: tool={tool_name}, "
            f"success=True, duration={duration:.3f}s"
        )
        
        return result
        
    except Exception as e:
        # Log errore esecuzione
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(
            f"Tool execution failed: tool={tool_name}, "
            f"error={str(e)}, duration={duration:.3f}s",
            exc_info=True
        )
        
        # Restituisci errore all'utente
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Error executing tool {tool_name}: {str(e)}",
                    )
                ],
                isError=True,
            )
        )


mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request
mcp._mcp_server.request_handlers[types.ReadResourceRequest] = _handle_read_resource


# Expose the FastAPI app for uvicorn
# For SSE transport (used by ChatGPT SDK), use sse_app()
# For Streamable HTTP transport, use streamable_http_app()
app = mcp.sse_app()

# Aggiungi middleware CORS all'app (deve essere prima di CSP)
# Il middleware CORS permette il caricamento di risorse (JS, CSS) da origini diverse
# necessario quando il widget viene caricato da ChatGPT che ha un'origine diversa
app.add_middleware(CORSMiddleware)

# Aggiungi middleware CSP all'app
# Il middleware aggiunge Content Security Policy headers per prevenire attacchi XSS
app.add_middleware(CSPMiddleware)

# Root route handler - provides information about available endpoints
async def root_handler(request):
    """Root endpoint that provides information about the server."""
    widget_names = [w.identifier for w in widgets]
    widgets_list = "\n".join([f"    <li><code>{name}</code> - {WIDGETS_BY_ID[name].title}</li>" for name in widget_names])
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Electronics MCP Server</title>
    <style>
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{ color: #2563eb; }}
        code {{
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: ui-monospace, monospace;
        }}
        ul {{ padding-left: 20px; }}
        .endpoint {{ 
            background: #f9fafb;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }}
        .endpoint strong {{ color: #059669; }}
    </style>
</head>
<body>
    <h1>Electronics MCP Server</h1>
    <p>Version: <code>{__version__}</code></p>
    <p>MCP Protocol Version: 2024-11-05</p>
    
    <h2>Available Endpoints</h2>
    <div class="endpoint">
        <strong>GET /</strong> - This page (server information)
    </div>
    <div class="endpoint">
        <strong>GET /mcp</strong> - SSE stream for MCP protocol
    </div>
    <div class="endpoint">
        <strong>POST /mcp/messages?sessionId=...</strong> - Send follow-up messages for an active session
    </div>
    <div class="endpoint">
        <strong>GET /assets/*</strong> - Static files (HTML, JS, CSS) from the assets directory
    </div>
    <div class="endpoint">
        <strong>GET /proxy-image?url=...</strong> - Proxy per immagini esterne (risolve problema ORB/CORS). 
        Accetta parametro <code>url</code> (URL-encoded) dell'immagine da proxyare.
    </div>
    
    <h2>Available Widgets ({len(widgets)})</h2>
    <ul>
{widgets_list}
    </ul>
    
    <h2>Documentation</h2>
    <p>See <code>electronics_server_python/README.md</code> for more information.</p>
</body>
</html>"""
    return StarletteHTMLResponse(content=html_content)

# Health check endpoint - returns 200 OK for health checks (useful for Render, etc.)
async def health_handler(request):
    """Health check endpoint for monitoring and load balancers."""
    return Response(content="OK", status_code=200, media_type="text/plain")

# Serve static files from assets directory
if ASSETS_DIR.exists():
    # Serve from /assets/ for explicit asset access
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR), html=False), name="assets")
    logger.info(f"Static files available at /assets/ (serving from {ASSETS_DIR})")
else:
    logger.warning(f"Assets directory not found at {ASSETS_DIR}. Static files will not be served.")

# Add routes using Starlette's add_route (since sse_app() returns a Starlette app, not FastAPI)
app.add_route("/", root_handler, methods=["GET"])
app.add_route("/health", health_handler, methods=["GET"])
app.add_route("/proxy-image", proxy_image_handler, methods=["GET"])
app.add_route("/proxy-image", proxy_image_options_handler, methods=["OPTIONS"])


if __name__ == "__main__":
    """
    Permette di eseguire il server direttamente con: python main.py
    Per produzione, usa invece: uvicorn electronics_server_python.main:app --host 0.0.0.0 --port $PORT
    """
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")
    
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Access the server at http://{host}:{port}")
    logger.info(f"MCP endpoint: http://{host}:{port}/mcp")
    
    uvicorn.run(app, host=host, port=port)

