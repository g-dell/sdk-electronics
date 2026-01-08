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

load_dotenv()

# Configurazione logging per activity logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import mcp.types as types
from fastapi import Request, FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from mcp.server.fastmcp import FastMCP
from starlette.staticfiles import StaticFiles
from starlette.routing import Mount
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import BaseModel, ConfigDict, Field, ValidationError


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
        logger.error(f"MotherDuck configuration error: {e}")
        return []
    except Exception as e:
        # Altri errori (es. connessione, query, ecc.)
        logger.error(f"Error retrieving products from MotherDuck: {e}", exc_info=True)
        return []


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


class CSPMiddleware(BaseHTTPMiddleware):
    """
    Middleware per aggiungere Content Security Policy (CSP) headers alle risposte HTTP.
    
    CSP previene attacchi XSS limitando le risorse che possono essere caricate ed eseguite.
    """
    
    async def dispatch(self, request: Request, call_next):
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

    contents = [
        types.TextResourceContents(
            uri=widget.template_uri,
            mimeType=MIME_TYPE,
            text=widget.html,
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
        else:
            # Widget di visualizzazione che non richiedono input
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

# Aggiungi middleware CSP all'app
# Il middleware aggiunge Content Security Policy headers per prevenire attacchi XSS
app.add_middleware(CSPMiddleware)

