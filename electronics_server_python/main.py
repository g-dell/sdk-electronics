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


# Mapping delle categorie principali ai tag associati (stesso mapping del frontend)
CATEGORY_MAPPING = {
    "Video & TV": [
        "tv", "televisions", "tv accessories", "tv mounts", "projectors",
        "video projectors", "dvd players", "blu-ray players", "blu-ray",
        "video", "home theater"
    ],
    "Informatica": [
        "computers", "desktop computers", "monitors", "tablets",
        "printers", "scanners", "computer accessories", "pc components",
        "input devices", "keyboards", "mice", "laptops"
    ],
    "Audio": [
        "audio", "speakers", "wireless speakers", "bluetooth speakers",
        "headphones", "home audio", "home theater", "home theater systems",
        "microphones", "amplifiers", "stereos", "portable audio"
    ],
}


def filter_products_by_category(products: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
    """
    Filtra i prodotti per categoria basandosi sui tag/categorie nel database.
    
    Logica semplificata: cerca se uno dei tag della categoria è contenuto in una delle
    categorie del prodotto (match parziale case-insensitive).
    
    Args:
        products: Lista di prodotti dal database
        category: Nome della categoria (es. "Video & TV", "Informatica", "Audio")
                  o tag specifico (es. "tv", "televisions")
    
    Returns:
        Lista filtrata di prodotti che appartengono alla categoria specificata
    """
    if not products or not category:
        return products
    
    # Normalizza la categoria richiesta (case-insensitive)
    category_lower = category.lower().strip()
    
    # Trova i tag da cercare nel mapping
    search_tags = []
    matched_main_category = None
    
    # Cerca se la categoria richiesta corrisponde a una categoria principale o a un tag
    for main_category, tags in CATEGORY_MAPPING.items():
        if category_lower == main_category.lower():
            # La categoria richiesta è una categoria principale - usa tutti i tag
            search_tags = [t.lower().strip() for t in tags]
            matched_main_category = main_category
            break
        elif category_lower in [t.lower() for t in tags]:
            # La categoria richiesta è uno dei tag di una categoria principale
            # IMPORTANTE: Se l'utente chiede un tag specifico (es. "tv"), usa solo tag strettamente correlati
            # per evitare match ambigui (es. "home theater" è sia in Video & TV che in Audio)
            matched_main_category = main_category
            
            # Se il tag richiesto è specifico (es. "tv", "speakers"), filtra i tag per evitare ambiguità
            if category_lower in ["tv", "televisions"]:
                # Per "tv", usa solo tag strettamente correlati a TV, escludendo "home theater" che è ambiguo
                search_tags = [t.lower().strip() for t in tags if t.lower() not in ["home theater", "home theater systems"]]
                # Aggiungi sempre il tag richiesto stesso
                if category_lower not in search_tags:
                    search_tags.append(category_lower)
            elif category_lower in ["speakers", "wireless speakers", "bluetooth speakers", "headphones", "audio"]:
                # Per prodotti audio specifici, escludi "home theater" che potrebbe matchare prodotti TV
                search_tags = [t.lower().strip() for t in tags if t.lower() not in ["home theater", "home theater systems"]]
                # Aggiungi sempre il tag richiesto stesso
                if category_lower not in search_tags:
                    search_tags.append(category_lower)
            else:
                # Per altri tag, usa tutti i tag della categoria principale
                search_tags = [t.lower().strip() for t in tags]
            break
    
    # Se non trovata nel mapping, usa la categoria stessa come tag da cercare
    if not search_tags:
        search_tags = [category_lower]
        logger.info(f"Category '{category}' not in mapping, using as direct search tag")
    else:
        logger.info(f"Category '{category}' matched to '{matched_main_category}', searching for tags: {search_tags[:5]}...")
    
    filtered_products = []
    products_without_categories = 0
    
    for product in products:
        # Estrai tutte le categorie/tag del prodotto (da categories o primaryCategories)
        product_categories_raw = []
        
        # Prova categories (campo principale nel database)
        if product.get("categories"):
            if isinstance(product["categories"], list):
                product_categories_raw.extend([str(cat).strip() for cat in product["categories"]])
            elif isinstance(product["categories"], str):
                product_categories_raw.extend([cat.strip() for cat in product["categories"].split(",")])
        
        # Prova primaryCategories (fallback)
        if product.get("primaryCategories"):
            if isinstance(product["primaryCategories"], list):
                product_categories_raw.extend([str(cat).strip() for cat in product["primaryCategories"]])
            elif isinstance(product["primaryCategories"], str):
                product_categories_raw.extend([cat.strip() for cat in product["primaryCategories"].split(",")])
        
        # Normalizza le categorie del prodotto (lowercase)
        product_categories = [cat.lower().strip() for cat in product_categories_raw if cat]
        
        # Se il prodotto non ha categorie, salta
        if not product_categories:
            products_without_categories += 1
            continue
        
        # Verifica se almeno uno dei tag da cercare matcha con una categoria del prodotto
        # Match semplice: controlla se il tag è contenuto nella categoria (o viceversa per tag lunghi)
        matches = False
        
        # Se stiamo cercando "tv" o "televisions", verifica che il prodotto non sia principalmente audio
        # (per evitare che prodotti audio con "home theater" vengano inclusi)
        if category_lower in ["tv", "televisions"]:
            # Controlla se il prodotto ha categorie audio esclusive (senza categorie video)
            has_audio_only = False
            has_video_tags = False
            
            # Tag strettamente video/TV
            video_tags = ["tv", "televisions", "television", "projector", "video", "dvd", "blu-ray", "blu ray"]
            # Tag strettamente audio
            audio_tags = ["speaker", "headphone", "microphone", "amplifier", "stereo", "portable audio"]
            
            for product_cat in product_categories:
                product_cat_lower = product_cat.lower()
                # Controlla se ha tag video
                if any(video_tag in product_cat_lower for video_tag in video_tags):
                    has_video_tags = True
                # Controlla se ha solo tag audio (escludendo "home theater" che è ambiguo)
                if any(audio_tag in product_cat_lower for audio_tag in audio_tags):
                    has_audio_only = True
            
            # Se il prodotto ha solo tag audio e nessun tag video, escludilo quando cerchiamo TV
            if has_audio_only and not has_video_tags:
                continue
        
        for search_tag in search_tags:
            search_tag_clean = search_tag.lower().strip()
            
            for product_cat in product_categories:
                product_cat_clean = product_cat.lower().strip()
                
                # Match esatto
                if search_tag_clean == product_cat_clean:
                    matches = True
                    break
                
                # Match parziale: il tag è contenuto nella categoria del prodotto
                # Es: "tv" matcha "tv mounts", "tv accessories & parts", "tv ceiling & wall mounts"
                # IMPORTANTE: Evita match ambigui - "tv" non deve matchare "home theater" se stiamo cercando TV specifiche
                if search_tag_clean in product_cat_clean:
                    # Se stiamo cercando "tv" o "televisions", escludi match con "home theater" che è ambiguo
                    # a meno che il prodotto non abbia anche tag video espliciti
                    if category_lower in ["tv", "televisions"] and "home theater" in product_cat_clean:
                        # Verifica se il prodotto ha anche tag video espliciti
                        has_explicit_video_tag = any(
                            video_tag in cat.lower() 
                            for cat in product_categories 
                            for video_tag in ["tv", "televisions", "television", "projector", "video"]
                        )
                        if not has_explicit_video_tag:
                            # Skip questo match se il prodotto ha solo "home theater" senza tag video espliciti
                            continue
                    matches = True
                    break
                
                # Match parziale inverso: la categoria è contenuta nel tag (per tag composti)
                # Es: "televisions" contiene "tv" quando cerchiamo "tv"
                # IMPORTANTE: Evita match ambigui anche qui
                if len(search_tag_clean) > 3 and product_cat_clean in search_tag_clean:
                    # Se stiamo cercando "tv" o "televisions", escludi match con "home theater"
                    if category_lower in ["tv", "televisions"] and "home theater" in search_tag_clean:
                        continue
                    matches = True
                    break
            
            if matches:
                break
        
        if matches:
            filtered_products.append(product)
    
    # Log risultati
    if filtered_products:
        # Log dettagliato per debug quando si cerca "tv" per verificare che non includa prodotti audio
        if category_lower in ["tv", "televisions"]:
            sample_names = [p.get("name", "Unknown")[:30] for p in filtered_products[:5]]
            logger.info(
                f"✅ Filter matched {len(filtered_products)}/{len(products)} products for category '{category}'. "
                f"Sample products: {sample_names}. "
                f"Showing only TV-related products (audio products excluded)."
            )
        else:
            logger.info(
                f"✅ Filter matched {len(filtered_products)}/{len(products)} products for category '{category}'. "
                f"Showing only filtered products (no unrelated products will be added)."
            )
    else:
        logger.warning(
            f"❌ Filter found 0 products for category '{category}'. "
            f"Total products: {len(products)}, Products without categories: {products_without_categories}. "
            f"Search tags: {search_tags[:5]}. "
            f"IMPORTANT: Will return empty list instead of adding unrelated products."
        )
        # Log esempi di categorie reali per debugging
        if products:
            all_categories = set()
            for product in products[:10]:
                cats = []
                if product.get("categories"):
                    if isinstance(product["categories"], list):
                        cats = [str(c).strip().lower() for c in product["categories"]]
                    elif isinstance(product["categories"], str):
                        cats = [c.strip().lower() for c in product["categories"].split(",")]
                all_categories.update(cats)
            
            logger.warning(f"Sample categories in database: {sorted(list(all_categories))[:15]}")
    
    return filtered_products


async def get_products_from_motherduck(category: str = None):
    """
    Recupera i prodotti elettronici dal database MotherDuck, opzionalmente filtrati per categoria.
    
    Args:
        category: Categoria opzionale per filtrare i prodotti (es. "Video & TV", "tv", "Informatica")
    
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
            
            # Filtra per categoria se specificata
            if category:
                original_count = len(products)
                logger.info(f"🔍 Applying category filter '{category}' to {original_count} products")
                products = filter_products_by_category(products, category)
                filtered_count = len(products)
                logger.info(f"✅ Filter result: {filtered_count}/{original_count} products match category '{category}'")
                
                if filtered_count == 0 and original_count > 0:
                    logger.warning(
                        f"⚠️ No products found for category '{category}'. "
                        f"Total products available: {original_count}. "
                        f"Check filter logic and category mapping."
                    )
                elif filtered_count == original_count:
                    logger.warning(
                        f"⚠️ Filter returned all products ({filtered_count}). "
                        f"This might indicate the filter is not working correctly."
                    )
            
            # Log per audit
            if products:
                logger.info(f"Retrieved {len(products)} products from MotherDuck" + (f" (filtered by category: {category})" if category else ""))
            else:
                logger.warning("No products retrieved from MotherDuck (empty result)" + (f" for category: {category}" if category else ""))
            
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

# Schema per tool che possono filtrare per categoria
CATEGORY_FILTER_INPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "description": "Categoria opzionale per filtrare i prodotti (es. 'Video & TV', 'tv', 'Informatica', 'Audio'). Se non specificata, vengono restituiti tutti i prodotti.",
        },
    },
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
            "Mostra un carosello interattivo di prodotti elettronici (massimo 12 prodotti). "
            "Usa questo tool quando l'utente vuole sfogliare prodotti in formato carosello o visualizzare "
            "una selezione di prodotti in modo interattivo. Puoi filtrare per categoria usando il parametro 'category' "
            "(es. 'Video & TV', 'tv', 'Informatica', 'Audio'). Restituisce un widget HTML con un carosello navigabile."
        ),
        "electronics-albums": (
            "Mostra una galleria di prodotti elettronici con visualizzazione a album. "
            "Usa questo tool quando l'utente chiede di vedere una galleria di prodotti, foto o immagini "
            "in formato album. Puoi filtrare per categoria usando il parametro 'category' "
            "(es. 'Video & TV', 'tv', 'Informatica', 'Audio'). Restituisce un widget HTML con una galleria interattiva."
        ),
        "electronics-list": (
            "Mostra una lista di prodotti elettronici. "
            "Usa questo tool quando l'utente chiede di vedere un elenco di prodotti o una lista semplice. "
            "Puoi filtrare per categoria usando il parametro 'category' "
            "(es. 'Video & TV', 'tv', 'Informatica', 'Audio'). Restituisce un widget HTML con una lista formattata di prodotti."
        ),
        "electronics-shop": (
            "Apre il negozio elettronico completo con funzionalità di shopping (massimo 24 prodotti). "
            "Usa questo tool quando l'utente vuole accedere al negozio completo, vedere prodotti con dettagli, "
            "o iniziare lo shopping. Puoi filtrare per categoria usando il parametro 'category' "
            "(es. 'Video & TV', 'tv', 'Informatica', 'Audio'). Restituisce un widget HTML con l'interfaccia completa del negozio."
        ),
        "product-list": (
            "Recupera e mostra la lista completa di prodotti elettronici dal database MotherDuck. "
            "Usa questo tool quando l'utente chiede di vedere tutti i prodotti disponibili, cercare prodotti, "
            "o visualizzare il catalogo completo. Puoi filtrare per categoria usando il parametro 'category' "
            "(es. 'Video & TV', 'tv', 'Informatica', 'Audio'). Restituisce dati strutturati JSON con i prodotti recuperati dal database, "
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
    # Tool che possono filtrare per categoria (recuperano prodotti da MotherDuck)
    tools_with_category_filter = {
        "product-list",
        "electronics-carousel",
        "electronics-albums",
        "electronics-list",
        "electronics-shop",
    }
    
    tools = [
        types.Tool(
            name=widget.identifier,
            title=widget.title,
            description=_tool_description(widget),
            inputSchema=deepcopy(
                CATEGORY_FILTER_INPUT_SCHEMA if widget.identifier in tools_with_category_filter
                else EMPTY_TOOL_INPUT_SCHEMA
            ),
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
    
    # Aggiungi il tool get_instructions che non è un widget
    tools.append(
        types.Tool(
            name="get_instructions",
            title="Get Instructions",
            description=(
                "Restituisce il contenuto testuale delle istruzioni (prompt) attualmente utilizzate dal server. "
                "Usa questo tool quando vuoi vedere quale prompt/instructions il server sta utilizzando. "
                "Restituisce il testo completo delle istruzioni dal file prompts/instructions.md."
            ),
            inputSchema=deepcopy(EMPTY_TOOL_INPUT_SCHEMA),
            annotations={
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        )
    )
    
    return tools


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
    
    # Gestione speciale per get_instructions (non è un widget)
    if tool_name == "get_instructions":
        try:
            # Valida che non ci siano argomenti inattesi
            if arguments:
                logger.warning(
                    f"Tool {tool_name}: Received unexpected arguments: {list(arguments.keys())}. "
                    "Ignoring arguments as this tool does not require input."
                )
            
            # Leggi il file prompts/instructions.md
            # Il file è nella root del progetto, non nella directory electronics_server_python
            instructions_path = Path(__file__).resolve().parent.parent / "prompts" / "instructions.md"
            
            if not instructions_path.exists():
                error_msg = f"Instructions file not found: {instructions_path}"
                logger.error(f"Tool {tool_name}: {error_msg}")
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
            
            # Leggi il contenuto del file
            instructions_text = instructions_path.read_text(encoding="utf-8")
            logger.info(f"Tool {tool_name}: Successfully read instructions from {instructions_path}")
            
            result = types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text=instructions_text,
                        )
                    ],
                    structuredContent={},
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
            error_msg = f"Error reading instructions file: {str(e)}"
            logger.error(f"Tool {tool_name}: {error_msg}", exc_info=True)
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
        # Estrai il parametro category dagli argomenti (se presente)
        category = arguments.get("category") if arguments else None
        if category:
            logger.info(f"Tool {tool_name}: Category filter requested: '{category}'")
        
        if tool_name == "product-list":
            # Tool che richiede accesso a MotherDuck
            logger.info(f"Tool {tool_name}: Fetching products from MotherDuck")
            products = await get_products_from_motherduck(category=category)
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
            # IMPORTANTE: Se viene passata una categoria, mostra SOLO i prodotti di quella categoria
            # Non aggiungere mai prodotti di altre categorie per "riempire" la galleria
            logger.info(f"Tool {tool_name}: Fetching products from MotherDuck and transforming to albums")
            products = await get_products_from_motherduck(category=category)
            if category:
                logger.info(
                    f"Tool {tool_name}: Filtered {len(products)} products for category '{category}'. "
                    "Showing only filtered products (no unrelated products will be added)."
                )
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
            
            # Note: category parameter is expected and already processed above
            # No need to warn about expected arguments
            
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
            # IMPORTANTE: Se viene passata una categoria, mostra SOLO i prodotti di quella categoria
            # Non aggiungere mai prodotti di altre categorie per "riempire" la lista/carosello
            logger.info(f"Tool {tool_name}: Fetching products from MotherDuck and transforming to places")
            products = await get_products_from_motherduck(category=category)
            
            # Per electronics-carousel, limita a 12 prodotti se viene passata una categoria
            # IMPORTANTE: Non aggiungere prodotti di altre categorie se il filtro ne trova meno di 12
            # Il limite è un MASSIMO, non un obbligo - se ci sono solo 5 prodotti filtrati, mostra solo quelli
            if category and tool_name != "electronics-carousel":
                logger.info(
                    f"Tool {tool_name}: Filtered {len(products)} products for category '{category}'. "
                    "Showing only filtered products (no unrelated products will be added)."
                )
            if tool_name == "electronics-carousel" and category:
                MAX_CAROUSEL_PRODUCTS = 12
                original_count = len(products)
                if original_count > MAX_CAROUSEL_PRODUCTS:
                    products = products[:MAX_CAROUSEL_PRODUCTS]
                    logger.info(
                        f"Tool {tool_name}: Limited products from {original_count} to {len(products)} "
                        f"(max {MAX_CAROUSEL_PRODUCTS} for carousel with category filter)"
                    )
                else:
                    logger.info(
                        f"Tool {tool_name}: Found {original_count} products for category '{category}' "
                        f"(showing all {original_count}, no need to add unrelated products)"
                    )
            
            places = transform_products_to_places(products)
            place_count = len(places) if places else 0
            if place_count == 0:
                # Se la lista è vuota, potrebbe essere dovuto a:
                # 1. Errore precedente (pandas mancante, token mancante, ecc.) - già loggato come ERROR/WARNING
                # 2. Database vuoto - comportamento normale
                # 3. Filtro categoria che non ha trovato prodotti
                logger.warning(
                    f"Tool {tool_name}: No products retrieved from MotherDuck. "
                    "Widget will display empty places list. "
                    "Check previous logs for errors (e.g., pandas missing, MOTHERDUCK_TOKEN not configured, or database connection issues)."
                )
            else:
                logger.info(f"Tool {tool_name}: Retrieved {len(products)} products, transformed to {place_count} places")
            
            # Note: category parameter is expected and already processed above
            # No need to warn about expected arguments
            
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
        elif tool_name == "electronics-shop":
            # electronics-shop potrebbe recuperare prodotti se necessario
            # Per ora non recupera prodotti direttamente, ma potrebbe in futuro
            # Se ha category parameter, potrebbe essere necessario recuperare prodotti
            if category:
                logger.info(f"Tool {tool_name}: Category filter requested but electronics-shop doesn't fetch products directly")
                # Potremmo voler recuperare prodotti in futuro per electronics-shop
                # Per ora, ignora il filtro categoria per electronics-shop
            
            # Valida che non ci siano altri argomenti inattesi (category è accettato ma ignorato per ora)
            unexpected_args = [k for k in (arguments.keys() if arguments else []) if k != "category"]
            if unexpected_args:
                logger.warning(
                    f"Tool {tool_name}: Received unexpected arguments: {unexpected_args}. "
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

