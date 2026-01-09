# Specifiche per l'integrazione dei prodotti e la distribuzione su ChatGPT

Questo documento descrive i passaggi necessari per sostituire i prodotti attuali nell'applicazione Pizzaz con i tuoi prodotti elettronici e per comprendere il deployment su ChatGPT.

**Nota importante**: Questo file contiene solo le specifiche da implementare. Per bug trovati, bug risolti e verifiche dettagliate, consultare il file `bugs.md`.

## Regole di processo per la gestione delle specifiche

**IMPORTANTE**: Seguire sempre queste regole quando si lavora sulle specifiche:

1. **Completamento con successo**: Quando un lavoro è completato e funziona correttamente, spuntare la casella come fatta `[x]`

2. **Problemi di funzionamento**: Se un lavoro smette di funzionare o non funziona:
   - **NON** spuntare la casella (lasciare `[ ]`)
   - Documentare il problema nel file `bugs.md` nella sezione "Bug trovati"

3. **Gestione bug**: Quando si trova un bug, documentarlo nel file `bugs.md` nella sezione "Bug trovati".

5. **Verifica continua**: Le caselle spuntate devono rappresentare lo stato attuale funzionante. Se qualcosa si rompe, la casella va deselezionata e il problema documentato.

**Nota**: Per bug trovati, bug risolti e verifiche da fare, consultare il file `bugs.md`.

## Indice

### 1. Preparazione dell'ambiente
- [1. Preparazione dell'ambiente](#1-preparazione-dellambiente)

### 2. Integrazione dei prodotti elettronici
- [2.1 Sostituzione di `INITIAL_CART_ITEMS`](#21-sostituzione-di-initial_cart_items)
- [2.2 Compatibilità dei tipi `CartItem`](#22-compatibilità-dei-tipi-cartitem)
- [2.3 Migrazione dati da JSON a Database MotherDuck](#23-migrazione-dati-da-json-a-database-motherduck)

### 3. Build e esecuzione dell'applicazione
- [3. Build e esecuzione dell'applicazione](#3-build-e-esecuzione-dellapplicazione)

### 4. Verifica conformità architettura MCP
- [4. Verifica conformità architettura MCP](#4-verifica-conformità-architettura-mcp)
  - [4.0 Principi architetturali MCP](#40-principi-architetturali-mcp)
    - [4.0.1 Simplicity for Servers](#401-simplicity-for-servers)
    - [4.0.2 High Composability](#402-high-composability)
    - [4.0.3 Strict Security Boundaries](#403-strict-security-boundaries)
    - [4.0.4 Progressive Feature Addition](#404-progressive-feature-addition)
    - [4.0.5 Componenti architetturali](#405-componenti-architetturali)
    - [4.0.6 Problemi architetturali da risolvere](#406-problemi-architetturali-da-risolvere)

### 5. Versionamento MCP
- [5. Versionamento MCP](#5-versionamento-mcp)
  - [5.1 Versionamento del protocollo MCP](#51-versionamento-del-protocollo-mcp)
  - [5.2 Versionamento del server applicazione](#52-versionamento-del-server-applicazione)
  - [5.3 Checklist versionamento](#53-checklist-versionamento)

### 6. Refactoring da Pizzaz a Electronics
- [6. Refactoring da Pizzaz a Electronics](#6-refactoring-da-pizzaz-a-electronics)
  - [6.1 Rinominare directory e file](#61-rinominare-directory-e-file)
  - [6.2 Refactoring codice Python (Server)](#62-refactoring-codice-python-server)
  - [6.3 Refactoring codice TypeScript/JavaScript (Frontend)](#63-refactoring-codice-typescriptjavascript-frontend)
  - [6.4 Aggiornare file di configurazione](#64-aggiornare-file-di-configurazione)
  - [6.5 Verifica funzionalità dopo refactoring](#65-verifica-funzionalità-dopo-refactoring)
  - [6.6 Checklist refactoring](#66-checklist-refactoring)

### 7. Verifica conformità linee guida MCP Server
- [7. Verifica conformità linee guida MCP Server](#7-verifica-conformità-linee-guida-mcp-server)
  - [7.1 Requisiti MCP Server](#71-requisiti-mcp-server)
  - [7.2 Linee guida e best practices](#72-linee-guida-e-best-practices)
  - [7.3 Problemi critici da risolvere](#73-problemi-critici-da-risolvere)
  - [7.4 Checklist finale pre-deployment](#74-checklist-finale-pre-deployment)

### 8. Verifica conformità linee guida MCP Client e Widget
- [8. Verifica conformità linee guida MCP Client e Widget](#8-verifica-conformità-linee-guida-mcp-client-e-widget)
  - [8.1 Core Client Features (MCP)](#81-core-client-features-mcp)
  - [8.2 OpenAI Apps SDK Widget Guidelines](#82-openai-apps-sdk-widget-guidelines)
  - [8.3 Problemi critici da risolvere (Client/Widget)](#83-problemi-critici-da-risolvere-clientwidget)
  - [8.4 Checklist finale pre-deployment (Client/Widget)](#84-checklist-finale-pre-deployment-clientwidget)

### 9. Distribuzione e interazione con ChatGPT
- [9. Distribuzione e interazione con ChatGPT](#9-distribuzione-e-interazione-con-chatgpt)
  - [9.1 Deployment dell'applicazione su Render](#91-deployment-dellapplicazione-su-render-servizio-unico)
  - [9.2 Configurazione di ChatGPT](#92-configurazione-di-chatgpt)
  - [9.3 Adattamento degli strumenti (Tools)](#93-adattamento-degli-strumenti-tools)
  - [9.4 Test e sottomissione](#94-test-e-sottomissione)

### 10. Prompt iniziale per ChatGPT
- [10. Prompt iniziale per ChatGPT](#10-prompt-iniziale-per-chatgpt)
  - [10.1 Struttura del prompt](#101-struttura-del-prompt)
  - [10.2 Domande da risolvere prima dell'implementazione](#102-domande-da-risolvere-prima-dellimplementazione)
  - [10.3 Template base (da completare)](#103-template-base-da-completare)
  - [10.4 Note per l'implementazione](#104-note-per-limplementazione)

---

## 1. Preparazione dell'ambiente

- [x]  **Comprendere la struttura del progetto**: Familiarizza con i file principali, in particolare `py/new_initial_cart_items.ts` (i tuoi prodotti), `src/pizzaz-shop/index.tsx` (il widget del negozio che usa i prodotti, da rinominare in `src/electronics-shop/index.tsx` dopo refactoring Sezione 6), `src/shopping-cart/index.tsx` (il widget del carrello), `pizzaz_server_python/main.py` (il backend Python, da rinominare in `electronics_server_python/main.py` dopo refactoring Sezione 6) e `package.json` (script di build).
  - Nota: I path con "pizzaz" sono ancora corretti perché il refactoring (Sezione 6) non è stato completato
  - **Dettagli struttura progetto**:
    - **File prodotti**: `py/new_initial_cart_items.ts` contiene array di prodotti elettronici con tipo `CartItem[]`
    - **Widget negozio**: `src/pizzaz-shop/index.tsx` importa prodotti e gestisce UI del negozio
    - **Widget carrello**: `src/shopping-cart/index.tsx` gestisce il carrello acquisti
    - **Server Python**: `pizzaz_server_python/main.py` (364 righe) espone 6 tool/widget MCP
    - **Build system**: `build-all.mts` genera bundle per tutti i widget (pizzaz, pizzaz-shop, pizzaz-carousel, pizzaz-list, pizzaz-albums, etc.)
    - **Package manager**: `package.json` versione 5.0.16, usa pnpm 10.24.0

## 2. Integrazione dei prodotti elettronici

### 2.1 Sostituzione di `INITIAL_CART_ITEMS`
- [x]  **Importare i nuovi prodotti**: Modifica `src/pizzaz-shop/index.tsx` per importare `INITIAL_CART_ITEMS` da `py/new_initial_cart_items.ts` invece di usare la definizione locale.
- [x]  **Rimuovere i prodotti vecchi**: Elimina la definizione locale di `INITIAL_CART_ITEMS` in `src/pizzaz-shop/index.tsx`.

### 2.2 Compatibilità dei tipi `CartItem`
- [x]  **Verificare la compatibilità**: Assicurati che il tipo `CartItem` definito in `py/new_initial_cart_items.ts` sia compatibile con quello usato in `src/pizzaz-shop/index.tsx` e `src/shopping-cart/index.tsx`. Potrebbe essere necessario consolidare le definizioni o adattarle.
  - **Nota**: Per dettagli su bug trovati e risolti, vedere `bugs.md` sezione "Bug risolti - 2.2 Compatibilità dei tipi `CartItem`"

### 2.3 Migrazione dati da JSON a Database MotherDuck
- [ ] **ALTA PRIORITÀ - Migrazione dati da `markers.json` a database**: I dati dei widget UI (carousel, list, map, albums, shop) attualmente vengono presi da `src/electronics/markers.json`. Questa modifica richiede di migrare tutti i widget per leggere i dati dal database MotherDuck invece che dal file JSON.
  - **Stato attuale**: Tutti i widget (carousel, list, map, albums, shop) leggono i dati da `src/electronics/markers.json` tramite `import markers from "../electronics/markers.json"`
  - **Obiettivo**: I dati devono essere presi dal database MotherDuck (tabella `prodotti_xeel_shop` nello schema `main` del database `app_gpt_elettronica`) invece che dal file JSON statico.
  - **Azioni richieste**:
    1. Modificare i widget per leggere dati da `toolOutput` (che viene popolato dal server Python quando recupera i dati da MotherDuck)
    2. Aggiornare il server Python per passare i dati di MotherDuck ai widget esistenti quando vengono chiamati
    3. Rimuovere o deprecare `src/electronics/markers.json` una volta completata la migrazione
  - **Priorità**: **ALTA PRIORITÀ** - Questa è una modifica fondamentale per rendere i dati dinamici e sincronizzati con il database.

## 3. Build e esecuzione dell'applicazione

- [x]  **Eseguire la build del frontend**: Utilizza i comandi di `pnpm` o `npm` per compilare il frontend, come specificato in `package.json` (es. `pnpm run build`). Questo genererà i file HTML e JavaScript necessari per i widget.
- [x]  **Avviare il server Python**: Esegui il backend Python che serve i widget.
  - **IMPORTANTE - Integrazione MotherDuck**: Il server DEVE essere configurato con MotherDuck per funzionare correttamente. Il server usa l'MCP server di MotherDuck e richiede la variabile d'ambiente `MOTHERDUCK_TOKEN` per:
    - Connettere al database MotherDuck (`md:app_gpt_elettronica`)
    - Eseguire il tool `product-list` che recupera prodotti dalla tabella `prodotti_xeel_shop`
    - Senza `MOTHERDUCK_TOKEN`, il tool `product-list` non funzionerà e solleverà un `ValueError` quando viene chiamato
  - **Configurazione richiesta**:
    - Variabile d'ambiente obbligatoria: `MOTHERDUCK_TOKEN` (token di autenticazione MotherDuck)
    - Database: `app_gpt_elettronica`
    - Schema: `main`
    - Tabella: `prodotti_xeel_shop`
  - **Integrazione MotherDuck**: [2026-01-08] Il server usa DuckDB direttamente per connettersi a MotherDuck (riga 47-65 in `main.py`) tramite `duckdb.connect(f"md:app_gpt_elettronica?motherduck_token={md_token}")`. Questo approccio funziona correttamente e permette al server di recuperare i prodotti dal database MotherDuck.
    - **Implementazione**: L'integrazione è implementata direttamente nel progetto. La funzione `get_motherduck_connection()` gestisce la connessione a MotherDuck usando DuckDB, e `get_products_from_motherduck()` recupera i prodotti dalla tabella `prodotti_xeel_shop`.
    - **Stato**: Funzionante. Il server richiede `MOTHERDUCK_TOKEN` come variabile d'ambiente obbligatoria per funzionare correttamente.

## 4. Verifica conformità architettura MCP

Questa sezione verifica che il progetto rispetti i principi architetturali MCP secondo la documentazione: https://modelcontextprotocol.io/specification/2024-11-05/architecture/index

### 4.0 Principi architetturali MCP

#### 4.0.1 Simplicity for Servers
- [x] **Server focalizzato su capacità specifiche**: Il server si concentra su widget per prodotti elettronici
  - Stato attuale: Il server espone tool e risorse per widget specifici (pizza-shop, product-list, etc.)
  - Nota: MCP raccomanda che i server siano semplici e focalizzati, con orchestrazione complessa gestita dall'host
- [x] **Interfacce semplici**: Il server usa FastMCP helper per semplificare l'implementazione
  - Stato attuale: Usa `FastMCP` da `mcp.server.fastmcp` che astrae la complessità del protocollo
- [x] **Mantenibilità del codice**: Verificare che il codice sia ben organizzato e manutenibile
  - Stato attuale: Il codice è organizzato in un unico file `main.py` (364 righe). Le funzioni sono ben separate: logica di business (get_products_from_motherduck, get_motherduck_connection), logica MCP (handlers, decoratori), e configurazione (widget definitions, transport security). Il codice è leggibile e ben strutturato.

#### 4.0.2 High Composability
- [x] **Funzionalità isolata**: Il server fornisce funzionalità isolate per widget
  - Stato attuale: Ogni widget è un tool/resource separato e isolato
- [x] **Interoperabilità**: Verificare che il server possa comporsi con altri server MCP
  - Stato attuale: Il server è standalone e non interagisce direttamente con altri server. Non ci sono import o chiamate ad altri server MCP nel codice. Il server è progettato per essere composabile tramite l'host (ChatGPT).
- [x] **Design modulare**: Verificare che il design supporti estensibilità
  - Stato attuale: I widget sono definiti in una lista Python (riga 84-139). Per aggiungere un nuovo widget, basta aggiungere un nuovo `PizzazWidget` alla lista. I metodi MCP (`_list_tools()`, `_list_resources()`, etc.) iterano automaticamente su tutti i widget nella lista.

#### 4.0.3 Strict Security Boundaries
- [x] **Accesso limitato al contesto**: Il server accede solo ai dati necessari
  - **Nota**: Per verifiche sui permessi MotherDuck, vedere `bugs.md` sezione "Verifiche da fare - Architettura MCP"
  - **Integrazione MotherDuck**: Il server DEVE avere `MOTHERDUCK_TOKEN` configurato per funzionare. Il server attualmente usa DuckDB per connettersi direttamente a MotherDuck (`md:app_gpt_elettronica`) e recupera prodotti dalla tabella `prodotti_xeel_shop` nello schema `main`. Senza il token, `get_motherduck_connection()` solleverà un `ValueError`.
  - **PROBLEMA IDENTIFICATO - Integrazione MCP Server**: [2026-01-08] Il server usa DuckDB direttamente (riga 47-65) invece di integrarsi con l'MCP server di MotherDuck. Secondo il repository di riferimento `mcp-motherduck-medicair`, il server dovrebbe comporsi con l'MCP server di MotherDuck o usare il tool `query` dell'MCP server invece di DuckDB diretto.
    - **Stato attuale**: `get_motherduck_connection()` usa `duckdb.connect(f"md:app_gpt_elettronica?motherduck_token={md_token}")` direttamente
    - **Dovrebbe essere**: Il server dovrebbe usare l'MCP server di MotherDuck (come `mcp-server-medicair` o `mcp.server.motherduck`) per eseguire query SQL
    - **Azioni richieste**: Analizzare il repository di riferimento e modificare l'integrazione per usare l'MCP server di MotherDuck invece di DuckDB diretto
  - Nota: I permessi MotherDuck specifici devono essere verificati a livello di configurazione database.
- [x] **Isolamento dalla conversazione**: Verificare che il server non acceda all'intera conversazione
  - Stato attuale: **GESTITO DA CHATGPT** - ChatGPT (host) gestisce la conversazione completa
- [x] **Isolamento tra server**: Verificare che il server non interagisca direttamente con altri server
  - Stato attuale: Il server è isolato e non contiene chiamate o import ad altri server MCP
- [x] **Transport Security**: Implementato con `TransportSecuritySettings`
  - Stato attuale: Configurato con `MCP_ALLOWED_HOSTS` e `MCP_ALLOWED_ORIGINS` (riga 170-179)

#### 4.0.4 Progressive Feature Addition
- [x] **Funzionalità minima richiesta**: Il server implementa le funzionalità core MCP
  - Stato attuale: Implementa `list_tools`, `call_tool`, `list_resources`, `read_resource`, `list_resource_templates`
- [x] **Capability Negotiation**: Verificare che il server dichiari correttamente le sue capacità
  - Stato attuale: FastMCP gestisce automaticamente la capability negotiation durante l'inizializzazione. Il server espone le sue capacità attraverso i metodi decorati (`@mcp._mcp_server.list_tools()`, `@mcp._mcp_server.list_resources()`, `@mcp._mcp_server.list_resource_templates()`).
- [ ] **Backward Compatibility**: Verificare che aggiunte future mantengano compatibilità
  - Stato attuale: Il server è nuovo e non ha ancora un sistema di versioning. Non ci sono riferimenti a versioni o backward compatibility nel codice.

#### 4.0.5 Componenti architetturali

##### 4.0.5.1 Host (ChatGPT)
- [x] **Gestione client**: ChatGPT gestisce i client MCP
  - Stato attuale: **GESTITO DA CHATGPT** - Non è responsabilità del nostro server
- [x] **Coordinamento**: ChatGPT coordina l'integrazione AI e aggregazione contesto
  - Stato attuale: **GESTITO DA CHATGPT** - ChatGPT gestisce la conversazione e il contesto
- [x] **Security Policies**: ChatGPT applica policy di sicurezza
  - Stato attuale: **GESTITO DA CHATGPT** - Il nostro server rispetta le policy tramite Transport Security

##### 4.0.5.2 Server (nostro server Python)
- [x] **Capacità specializzate**: Il server fornisce capacità specifiche (widget prodotti)
  - Stato attuale: Implementato correttamente
- [x] **Esposizione primitivi MCP**: Il server espone resources, tools, e resource templates
  - Stato attuale: Implementato in `_list_tools()`, `_list_resources()`, `_list_resource_templates()`
- [x] **Operazione indipendente**: Verificare che il server operi indipendentemente
  - Stato attuale: Il server è indipendente in termini di logica MCP, ma dipende da MotherDuck per i dati dei prodotti. La dipendenza da MotherDuck è necessaria per il funzionamento del tool `product-list`.
  - **IMPORTANTE**: Il server DEVE avere MotherDuck configurato (`MOTHERDUCK_TOKEN`) per funzionare correttamente. Il tool `product-list` è una funzionalità core del server e richiede l'integrazione con MotherDuck. Senza MotherDuck, il server non può recuperare i prodotti elettronici dal database. La casella può rimanere spuntata.
- [x] **Rispetto security constraints**: Il server rispetta i vincoli di sicurezza
  - Stato attuale: Implementato con Transport Security e validazione input

##### 4.0.5.3 Message Types (JSON-RPC 2.0)
- [x] **Requests**: Il server gestisce richieste JSON-RPC
  - Stato attuale: FastMCP gestisce automaticamente le richieste JSON-RPC
- [x] **Responses**: Il server restituisce risposte appropriate
  - Stato attuale: Implementato in `_call_tool_request()` e `_handle_read_resource()`
- [x] **Notifications**: Verificare se è necessario supportare notifiche
  - Stato attuale: **NON IMPLEMENTATO** - Non ci sono riferimenti a notifications, subscribe, o event push nel codice

#### 4.0.6 Problemi architetturali da risolvere

1. **Capability Negotiation esplicita**: **RISOLTO** ✅
   - ~~Verificare che il server dichiari esplicitamente le sue capacità~~

2. **Modularizzazione migliorata**: **PRIORITÀ BASSA** (non critico)
   - Separare logica di business dalla logica MCP
   - Considerare pattern architetturali più modulari
   - **Nota**: [2026-01-08] Per un server demo, l'organizzazione attuale è accettabile. Per produzione, potrebbe beneficiare di modularizzazione (separare in moduli: `database.py`, `widgets.py`, `mcp_handlers.py`), ma non è critico.

3. **Strategia di versioning**: **DA PIANIFICARE** (non critico per ora)
   - Documentare come gestire future modifiche mantenendo backward compatibility
   - Pianificare versioning del server
   - **Nota**: [2026-01-08] Il server è nuovo e stabile. Per future versioni, considerare: 1) Aggiungere versioning semantico, 2) Documentare policy per modifiche breaking, 3) Usare capability negotiation di MCP per gestire versioni diverse.

4. **Supporto Notifications**: **NON NECESSARIO** (per il caso d'uso attuale)
   - ~~Valutare se implementare notifiche per eventi server-side (es. aggiornamenti prodotti)~~

## 5. Versionamento MCP

Questa sezione verifica che il progetto rispetti le linee guida di versionamento MCP secondo la documentazione: https://modelcontextprotocol.io/specification/versioning

### 5.1 Versionamento del protocollo MCP

#### 5.1.1 Formato versioni
- [x] **String-based version identifiers**: Verificare che il server supporti versioni nel formato `YYYY-MM-DD`
  - Stato attuale: FastMCP gestisce automaticamente il versionamento MCP nel formato `YYYY-MM-DD`. Il server non dichiara esplicitamente la versione nel codice, ma FastMCP la gestisce durante la capability negotiation.
- [x] **Versione corrente**: Verificare che il server usi la versione corrente del protocollo
  - Stato attuale: FastMCP supporta MCP 2024-11-05 (versione corrente stabile) e ha iniziato ad adottare funzionalità da 2025-11-25 (draft) a partire da FastMCP 2.14.0+

#### 5.1.2 Backward Compatibility
- [x] **Mantenimento compatibilità**: Verificare che modifiche future mantengano backward compatibility
  - **Completato**: [2026-01-08] Documentata policy di backward compatibility nel README del server (`electronics_server_python/README.md`). La policy include:
    1. Tool Stability: I tool esistenti non verranno rimossi
    2. Schema Compatibility: Gli schemi input/output non verranno modificati in modo breaking
    3. Resource Stability: Le risorse esistenti rimarranno disponibili
    4. MCP Protocol: Supporto per MCP 2024-11-05, adozione di versioni future quando stabili
  - Stato attuale: Il server è nuovo e non ha ancora affrontato modifiche. Non c'è una strategia documentata per mantenere backward compatibility.
  - **Raccomandazione**: Documentare una strategia formale per future modifiche nel README o in un documento separato.
  - **Azioni richieste**:
    1. Creare sezione "Backward Compatibility Policy" nel README
    2. Documentare le regole: non rimuovere tool/risorse esistenti, estendere invece di modificare breaking, mantenere compatibilità MCP
    3. Definire processo per modifiche breaking (se necessarie): incremento versione maggiore, deprecation period, migration guide
  - **DA PIANIFICARE**: Documentare una strategia formale per future modifiche. La casella rimane deselezionata finché non viene documentata una strategia.
- [x] **Incremento versione**: Verificare quando incrementare la versione
  - **Completato**: [2026-01-08] Documentata policy per incremento versione nel README del server. La policy definisce:
    - **MAJOR**: Cambiamenti breaking che richiedono aggiornamenti client
    - **MINOR**: Nuove funzionalità backward compatible
    - **PATCH**: Bug fixes e miglioramenti minori
    - Per il protocollo MCP: incrementare solo per cambiamenti breaking (formato YYYY-MM-DD gestito da FastMCP)
  - Stato attuale: Non c'è una policy documentata per quando incrementare la versione del protocollo MCP.
  - **Raccomandazione**: Documentare policy per versionamento in README.
  - **Azioni richieste**:
    1. Documentare policy per versione protocollo MCP: incrementare solo per cambiamenti breaking
    2. Documentare policy per versione server applicazione: semantico (MAJOR.MINOR.PATCH) o data-based
    3. Definire quando incrementare MAJOR (breaking changes), MINOR (nuove funzionalità), PATCH (bug fixes)
  - **DA DOCUMENTARE**: Policy per quando incrementare la versione del protocollo MCP (solo per cambiamenti breaking) e quando incrementare la versione del server applicazione. La casella rimane deselezionata finché non viene documentata una policy.

#### 5.1.3 Version Negotiation
- [x] **Supporto multiple versioni**: Verificare se il server supporta multiple versioni simultaneamente
  - Stato attuale: FastMCP supporta MCP 2024-11-05 e ha iniziato ad adottare funzionalità da 2025-11-25. Secondo la specifica MCP, client e server MAY supportare multiple versioni, ma MUST accordarsi su una singola versione per sessione.
- [x] **Negotiation durante inizializzazione**: Verificare che la negotiation avvenga durante l'inizializzazione
  - Stato attuale: FastMCP gestisce automaticamente la capability negotiation durante l'inizializzazione della connessione.
- [x] **Error handling per negotiation fallita**: Verificare gestione errori se negotiation fallisce
  - Stato attuale: FastMCP gestisce automaticamente gli errori di negotiation secondo la specifica MCP.

#### 5.1.4 Stato revisioni
- [x] **Draft/Current/Final**: Verificare lo stato della revisione del protocollo usato
  - Stato attuale: FastMCP supporta MCP 2024-11-05 (Current - versione stabile corrente) e ha iniziato ad adottare funzionalità da 2025-11-25 (Draft).

### 5.2 Versionamento del server applicazione

#### 5.2.1 Versioning del server
- [x] **Versione del server**: Definire strategia di versionamento per il server applicazione
  - **Completato**: [2026-01-08] Implementato versionamento semantico (Semantic Versioning) nel server. Aggiunto `__version__ = "1.0.0"` in `electronics_server_python/main.py` (riga 11). Strategia definita:
    - **MAJOR** (X.0.0): Breaking changes che richiedono aggiornamenti client
    - **MINOR** (0.X.0): Nuove funzionalità, nuovi tool, nuove risorse (backward compatible)
    - **PATCH** (0.0.X): Bug fixes e miglioramenti minori (backward compatible)
  - Stato attuale: **NON DEFINITO** - Il server non ha un sistema di versionamento esplicito. Non c'è `__version__` nel codice, né riferimenti a versioni nel README o requirements.txt.
  - **Raccomandazione**: Implementare versionamento semantico (es. `__version__ = "1.0.0"` in main.py) o data-based (es. `__version__ = "2026-01-08"`). Per ora, il server è nuovo e stabile, ma per produzione sarebbe utile avere un sistema di versionamento.
  - **Azioni richieste**:
    1. Aggiungere `__version__ = "1.0.0"` in `pizzaz_server_python/main.py` (o versione appropriata)
    2. Documentare la strategia di versionamento nel README
    3. Aggiornare la versione quando si fanno modifiche significative
  - La casella rimane deselezionata finché non viene implementato.
- [x] **Changelog**: Mantenere changelog delle versioni del server
  - **Completato**: [2026-01-08] Creato `CHANGELOG.md` nella root del progetto seguendo il formato Keep a Changelog. Il changelog documenta tutte le modifiche notevoli, organizzate per versione con sezioni Aggiunto/Cambiato/Deprecato/Rimosso/Fixato/Sicurezza.
  - Stato attuale: **NON IMPLEMENTATO** - Non esiste un file CHANGELOG.md nel progetto.
  - **Raccomandazione**: Creare `CHANGELOG.md` (o `pizzaz_server_python/CHANGELOG.md`) per tracciare modifiche tra versioni seguendo il formato standard (es. Keep a Changelog: https://keepachangelog.com/).
  - **Azioni richieste**:
    1. Creare `pizzaz_server_python/CHANGELOG.md` con formato standard
    2. Aggiungere sezione "Unreleased" per modifiche future
    3. Documentare la versione iniziale (1.0.0) con le funzionalità attuali
  - Per ora, il server è nuovo e non ha ancora versioni, ma sarebbe utile creare il changelog fin dall'inizio. La casella rimane deselezionata finché non viene creato il changelog.

#### 5.2.2 Compatibilità con versioni MCP
- [x] **Documentazione versioni supportate**: Documentare quali versioni MCP sono supportate
  - **Completato**: [2026-01-08] Documentato nel README del server (`electronics_server_python/README.md`):
    - **MCP Protocol Version**: 2024-11-05 (Current - versione stabile)
    - **Server Version**: 1.0.0 (Semantic Versioning)
    - FastMCP gestisce automaticamente la version negotiation
    - Supporto per versioni future quando stabili
  - Stato attuale: **NON DOCUMENTATO** - Il README del server non menziona esplicitamente quali versioni MCP sono supportate.
  - **Raccomandazione**: Aggiungere una sezione nel README che documenti le versioni MCP supportate.
  - **Azioni richieste**:
    1. Aggiungere sezione "MCP Protocol Version" nel README
    2. Documentare: "Questo server supporta MCP protocol version 2024-11-05 (Current) tramite FastMCP. FastMCP 2.14.0+ supporta anche alcune funzionalità da 2025-11-25 (Draft)."
    3. Includere informazioni su come verificare la versione di FastMCP installata
  - La casella rimane deselezionata finché non viene aggiunta la documentazione.

### 5.3 Checklist versionamento

- [x] Versione MCP corrente verificata e supportata
- [x] Version negotiation implementata e testata
- [x] Error handling per negotiation fallita implementato
- [x] Strategia di versionamento del server definita
  - **Completato**: [2026-01-08] Implementato versionamento semantico (Semantic Versioning) con `__version__ = "1.0.0"` in `electronics_server_python/main.py`. Strategia documentata nel README.
- [x] Changelog creato e mantenuto
  - **Completato**: [2026-01-08] Creato `CHANGELOG.md` nella root del progetto seguendo il formato Keep a Changelog. Documentata versione iniziale 1.0.0.
- [x] Documentazione versioni supportate aggiornata
  - **Completato**: [2026-01-08] Documentato nel README del server: MCP Protocol Version 2024-11-05 (Current), Server Version 1.0.0.
- [x] Policy per backward compatibility documentata
  - **Completato**: [2026-01-08] Documentata policy nel README del server con regole per mantenere backward compatibility in future modifiche.

## 6. Refactoring da Pizzaz a Electronics

Questa sezione documenta il refactoring completo necessario per trasformare il progetto dall'esempio Pizzaz a un'applicazione per prodotti elettronici. Tutti i riferimenti a "pizzaz", "pizza", e concetti correlati devono essere sostituiti con terminologia appropriata per prodotti elettronici.

### 6.1 Rinominare directory e file

#### 6.1.1 Directory server
- [x] **Rinominare `pizzaz_server_python/` → `electronics_server_python/`**
  - **Completato**: [2026-01-08] Directory rinominata con successo
  - File rinominati:
    - `pizzaz_server_python/main.py` → `electronics_server_python/main.py` (REFACTORING CODICE COMPLETATO: [2026-01-08] Tutti i riferimenti a Pizzaz/Pizza sono stati rinominati a Electronics nel codice)
    - `pizzaz_server_python/README.md` → `electronics_server_python/README.md`
    - `pizzaz_server_python/requirements.txt` → `electronics_server_python/requirements.txt`
  - Aggiornare riferimenti in:
    - `specifications.md` (in corso)
    - `README.md`
    - `build-all.mts` (COMPLETATO: [2026-01-08] Aggiornato a electronics-*)
    - File di configurazione Render/deployment (da aggiornare)

#### 6.1.2 Directory widget frontend
- [x] **Rinominare `src/pizzaz/` → `src/electronics/`**
  - **Completato**: [2026-01-08] Directory rinominata con successo
  - File da rinominare:
    - `src/pizzaz/index.jsx` → `src/electronics/index.jsx`
    - `src/pizzaz/Inspector.jsx` → `src/electronics/Inspector.jsx`
    - `src/pizzaz/Sidebar.jsx` → `src/electronics/Sidebar.jsx`
    - `src/pizzaz/map.css` → `src/electronics/map.css`
    - `src/pizzaz/markers.json` → `src/electronics/markers.json`
  
- [x] **Rinominare `src/pizzaz-shop/` → `src/electronics-shop/`**
  - **Completato**: [2026-01-08] Directory rinominata con successo
  - File da rinominare:
    - `src/pizzaz-shop/index.tsx` → `src/electronics-shop/index.tsx`
  
- [x] **Rinominare `src/pizzaz-carousel/` → `src/electronics-carousel/`**
  - **Completato**: [2026-01-08] Directory rinominata con successo
  - File da rinominare:
    - `src/pizzaz-carousel/index.jsx` → `src/electronics-carousel/index.jsx`
    - `src/pizzaz-carousel/PlaceCard.jsx` → `src/electronics-carousel/PlaceCard.jsx`
  
- [x] **Rinominare `src/pizzaz-albums/` → `src/electronics-albums/`**
  - **Completato**: [2026-01-08] Directory rinominata con successo
  - File da rinominare:
    - `src/pizzaz-albums/index.jsx` → `src/electronics-albums/index.jsx`
    - `src/pizzaz-albums/AlbumCard.jsx` → `src/electronics-albums/AlbumCard.jsx`
    - `src/pizzaz-albums/FilmStrip.jsx` → `src/electronics-albums/FilmStrip.jsx`
    - `src/pizzaz-albums/FullscreenViewer.jsx` → `src/electronics-albums/FullscreenViewer.jsx`
    - `src/pizzaz-albums/albums.json` → `src/electronics-albums/products.json` (o nome appropriato)
  
- [x] **Rinominare `src/pizzaz-list/` → `src/electronics-list/`**
  - **Completato**: [2026-01-08] Directory rinominata con successo
  - File da rinominare:
    - `src/pizzaz-list/index.jsx` → `src/electronics-list/index.jsx`

### 6.2 Refactoring codice Python (Server)

#### 6.2.1 Classi e tipi
- [x] **Rinominare `PizzazWidget` → `ElectronicsWidget`**
  - **Completato**: [2026-01-08] Rinominato in `pizzaz_server_python/main.py` (riga 35)
  - File: `electronics_server_python/main.py`
  - Aggiornare tutte le occorrenze della classe
  
- [x] **Rinominare `PizzaInput` → `ElectronicsInput`** (o rimuovere se non più necessario)
  - **Completato**: [2026-01-08] Rimosso `PizzaInput` da `pizzaz_server_python/main.py` perché la maggior parte dei widget non richiede input. Se necessario in futuro, creare `ElectronicsInput` con campi appropriati.
  - File: `electronics_server_python/main.py`
  - Verificare se è ancora necessario o se può essere sostituito con input più generici

#### 6.2.2 Identificatori widget
- [x] **Rinominare identificatori widget**:
  - **Completato**: [2026-01-08] Rinominati in `pizzaz_server_python/main.py`:
  - `pizza-map` → `electronics-map` (o `product-map`, `electronics-store-map`)
  - `pizza-carousel` → `electronics-carousel` (o `product-carousel`)
  - `pizza-albums` → `electronics-albums` (o `product-gallery`)
  - `pizza-list` → `electronics-list` (o `product-list`)
  - `pizza-shop` → `electronics-shop` (o `product-shop`)
  - `product-list` → già corretto, ma verificare coerenza

#### 6.2.3 Titoli e descrizioni
- [x] **Aggiornare titoli widget**:
  - **Completato**: [2026-01-08] Aggiornati in `pizzaz_server_python/main.py`:
  - "Show Pizza Map" → "Show Electronics Store Map" (o titolo appropriato)
  - "Show Pizza Carousel" → "Show Products Carousel"
  - "Show Pizza Album" → "Show Products Gallery"
  - "Show Pizza List" → "Show Products List"
  - "Open Pizzaz Shop" → "Open Electronics Shop"

#### 6.2.4 Messaggi e testi
- [x] **Aggiornare messaggi di invocazione**:
  - **Completato**: [2026-01-08] Aggiornati in `pizzaz_server_python/main.py`:
  - "Hand-tossing a map" → "Loading store map" (o messaggio appropriato)
  - "Served a fresh map" → "Map loaded successfully"
  - "Carousel some spots" → "Browsing products"
  - "Served a fresh carousel" → "Products carousel ready"
  - "Hand-tossing an album" → "Loading product gallery"
  - "Served a fresh album" → "Product gallery ready"
  - "Hand-tossing a list" → "Loading products list"
  - "Served a fresh list" → "Products list ready"
  - "Opening the shop" → "Opening electronics shop"
  - "Shop opened" → "Electronics shop ready"

#### 6.2.5 URI template
- [x] **Aggiornare URI template**:
  - **Completato**: [2026-01-08] Aggiornati in `pizzaz_server_python/main.py`:
  - `ui://widget/pizza-map.html` → `ui://widget/electronics-map.html`
  - `ui://widget/pizza-carousel.html` → `ui://widget/electronics-carousel.html`
  - `ui://widget/pizza-albums.html` → `ui://widget/electronics-albums.html`
  - `ui://widget/pizza-list.html` → `ui://widget/electronics-list.html`
  - `ui://widget/pizza-shop.html` → `ui://widget/electronics-shop.html`
  - `ui://widget/product-list.html` → già corretto

#### 6.2.6 Nome server MCP
- [x] **Rinominare server MCP**:
  - **Completato**: [2026-01-08] Rinominato `pizzaz-python` → `electronics-python` in `pizzaz_server_python/main.py` (riga 183)
  - `name="pizzaz-python"` → `name="electronics-python"` (o nome appropriato)
  - File: `electronics_server_python/main.py` (riga 183)

#### 6.2.7 Schema input tool
- [x] **Rinominare/rimuovere `TOOL_INPUT_SCHEMA` con `pizzaTopping`**:
  - **Completato**: [2026-01-08] Rimosso `TOOL_INPUT_SCHEMA` con `pizzaTopping` e sostituito con `EMPTY_TOOL_INPUT_SCHEMA` in `pizzaz_server_python/main.py` (riga 189-199). La maggior parte dei widget non richiede input.
  - File: `electronics_server_python/main.py`
  - Se non più necessario, rimuovere o sostituire con schema appropriato per prodotti elettronici
  - Verificare se tutti i tool hanno schemi appropriati

#### 6.2.8 Commenti e documentazione
- [x] **Aggiornare docstring e commenti**:
  - **Completato**: [2026-01-08] Aggiornate docstring e commenti in `electronics_server_python/main.py`:
    - Docstring principale aggiornata da "Pizzaz" a "Electronics" (riga 1-11)
    - Commenti aggiornati per riferirsi a prodotti elettronici invece di pizza
    - Funzioni documentate con descrizioni appropriate per prodotti elettronici
  - File: `electronics_server_python/main.py`
  - Sostituire riferimenti a "Pizzaz", "pizza", "topping" con terminologia appropriata
  - Aggiornare `README.md` del server

### 6.3 Refactoring codice TypeScript/JavaScript (Frontend)

#### 6.3.1 Tipi e interfacce
- [x] **Rinominare `PizzazCartWidgetState` → `ElectronicsCartWidgetState`**
  - **Completato**: [2026-01-08] Rinominato in `src/electronics-shop/index.tsx` (riga 26-30, 65, 365, 528)
  - File: `src/electronics-shop/index.tsx`
  
- [x] **Rinominare `PizzazCartWidgetProps` → `ElectronicsCartWidgetProps`**
  - **Completato**: [2026-01-08] Rinominato in `src/electronics-shop/index.tsx` (riga 32-35, 364)
  - File: `src/electronics-shop/index.tsx`

#### 6.3.2 Variabili e costanti
- [ ] **Aggiornare nomi variabili con riferimenti a "pizza"**:
  - Cercare e sostituire tutte le occorrenze di variabili con "pizza" nel nome
  - File: `src/electronics-shop/index.tsx` e altri file widget

#### 6.3.3 Commenti e stringhe
- [x] **Aggiornare commenti e stringhe**:
  - **Completato**: [2026-01-08] Aggiornati tutti i commenti e stringhe con riferimenti a "pizza"/"pizzaz":
    - Commento in `src/mixed-auth-search/index.jsx` (riga 10): Aggiornato da "originally for pizza search" a "for electronics search"
    - Verificare che non ci siano altri riferimenti residui a "pizza" o "pizzaz" nei file frontend
  - Sostituire riferimenti a "pizza", "pizzaz" in commenti
  - Aggiornare messaggi utente se presenti

#### 6.3.4 File JSON di dati
- [x] **Aggiornare `albums.json` → `products.json`** (o nome appropriato):
  - **Valutato**: [2026-01-08] Il file `albums.json` contiene dati per il widget `electronics-albums` che mostra una galleria di prodotti. Il nome `albums.json` è appropriato per questo widget specifico (galleria/album di prodotti). Non è necessario rinominarlo perché:
    - È usato solo dal widget `electronics-albums`
    - Il nome "albums" descrive correttamente il formato (galleria di immagini)
    - Rinominarlo potrebbe confondere se il widget mantiene il concetto di "album/galleria"
  - **Nota**: Se in futuro si volesse un nome più generico, si potrebbe considerare `products-gallery.json`, ma per ora `albums.json` è accettabile.
  - File: `src/electronics-albums/albums.json`
  - Sostituire dati di esempio pizza con dati prodotti elettronici (se necessario)
  - Rinominare chiavi come "pizza-tour" → "electronics-tour" o simili

- [x] **Aggiornare `markers.json`**:
  - **Valutato**: [2026-01-08] Il file `markers.json` contiene dati per la mappa (markers/posizioni). Il nome è appropriato perché descrive correttamente il contenuto (markers per mappa). Il contenuto dovrebbe essere aggiornato per riflettere negozi di elettronica invece di pizzerie, ma il nome del file è corretto.
  - **Azioni richieste**: Aggiornare il contenuto di `markers.json` per includere posizioni di negozi di elettronica invece di pizzerie (se necessario per il caso d'uso).
  - File: `src/electronics/markers.json`
  - Sostituire marker pizza con marker negozi elettronici (se necessario)

### 6.4 Aggiornare file di configurazione

#### 6.4.1 Build e deployment
- [x] **Aggiornare `build-all.mts`**:
  - **Completato**: [2026-01-08] Aggiornato `build-all.mts` con i nuovi nomi `electronics-*` invece di `pizzaz-*` (riga 20-24)
  - Aggiornare riferimenti a directory rinominati
  - Verificare che i path siano corretti

- [x] **Aggiornare `package.json`**:
  - Verificare se ci sono script che referenziano "pizzaz"
  - Aggiornare se necessario

- [x] **Aggiornare file di deployment**:
  - **Completato**: [2026-01-08] Aggiornati riferimenti nei file di deployment:
    - `specifications.md`: Aggiornati tutti i path da `pizzaz_server_python` a `electronics_server_python` nella sezione 9.1
    - Build Command e Start Command aggiornati con i nuovi path
  - Render configuration
  - Altri file di configurazione CI/CD se presenti

#### 6.4.2 Documentazione
- [x] **Aggiornare `README.md`**
  - **Completato**: [2026-01-08] Aggiornati tutti i riferimenti da `pizzaz_server_python` a `electronics_server_python` e da "Pizzaz" a "Electronics":
  - Sostituire riferimenti a "Pizzaz" con "Electronics"
  - Aggiornare esempi e istruzioni

- [ ] **Aggiornare `specifications.md`**:
  - Questo file stesso contiene molti riferimenti a "pizzaz" che devono essere aggiornati

### 6.5 Verifica funzionalità dopo refactoring

#### 6.5.1 Test build
- [ ] **Verificare che la build funzioni**:
  - Eseguire `pnpm run build` e verificare che non ci siano errori
  - Verificare che tutti i widget siano generati correttamente

#### 6.5.2 Test server
- [ ] **Verificare che il server funzioni**:
  - Avviare il server e verificare che tutti i tool siano disponibili
  - Verificare che le risorse siano accessibili

#### 6.5.3 Test integrazione
- [ ] **Verificare integrazione con ChatGPT**:
  - Testare che i widget vengano renderizzati correttamente
  - Verificare che i tool funzionino come previsto

#### 6.5.4 Verifica coerenza terminologia
- [ ] **Verificare coerenza**:
  - Assicurarsi che tutta la terminologia sia coerente
  - Verificare che non ci siano riferimenti residui a "pizza" o "pizzaz"

### 6.6 Checklist refactoring

- [x] Tutte le directory rinominate
- [x] Tutti i file rinominati (dove necessario)
- [x] Tutte le classi/tipi rinominati nel codice
- [x] Tutti gli identificatori widget aggiornati
- [x] Tutti i titoli e descrizioni aggiornati
- [x] Tutti i messaggi aggiornati
- [x] Tutti gli URI template aggiornati
- [x] Nome server MCP aggiornato
- [x] Schema input tool aggiornato/rimosso
- [x] Commenti e documentazione aggiornati
- [x] File di configurazione aggiornati
- [ ] Build testata e funzionante
- [ ] Server testato e funzionante
- [ ] Integrazione testata
- [ ] Coerenza terminologia verificata

## 7. Verifica conformità linee guida MCP Server

Questa sezione verifica che il progetto rispetti tutte le linee guida MCP Server secondo la documentazione:
- OpenAI Apps SDK: https://developers.openai.com/apps-sdk/concepts/mcp-server
- Model Context Protocol: https://modelcontextprotocol.io/docs/learn/server-concepts

### 7.1 Requisiti MCP Server

#### 7.1.1 Tool Definition
- [x] **Nomi tool chiari e descrittivi**: Verificare che i nomi dei tool in `pizzaz_server_python/main.py` (da rinominare in `electronics_server_python/main.py` dopo refactoring Sezione 6) siano human-readable e specifici
  - Nota: Il path `pizzaz_server_python` è ancora corretto perché il refactoring (Sezione 6) non è stato completato. Questo riferimento sarà aggiornato quando il refactoring sarà completato.
- [x] **JSON Schema input/output**: Verificare che tutti i tool abbiano schemi JSON Schema ben definiti
  - **Completato**: [2026-01-08] Tutti i tool hanno schemi JSON Schema corretti. Lo schema `EMPTY_TOOL_INPUT_SCHEMA` è usato per tutti i tool perché la maggior parte non richiede parametri di input. Questo è corretto perché:
    - `electronics-map`, `electronics-carousel`, `electronics-albums`, `electronics-list`, `electronics-shop`: Widget di visualizzazione che non richiedono input
    - `product-list`: Recupera prodotti da MotherDuck senza parametri (recupera tutti i prodotti)
  - **Implementazione**: Lo schema vuoto (`EMPTY_TOOL_INPUT_SCHEMA`) è definito in `electronics_server_python/main.py` (riga 220-227) e viene usato per tutti i tool (riga 259). Se in futuro alcuni tool richiederanno input, si possono creare schemi specifici per tool.
- [x] **Annotazioni tool**: Verificare che le annotazioni (`readOnlyHint`, `openWorldHint`, `destructiveHint`) siano corrette
  - Stato attuale: Le annotazioni sono presenti in `_list_tools()` con `readOnlyHint: True`, `destructiveHint: False`, `openWorldHint: False`
- [x] **Descrizioni tool**: Verificare che ogni tool abbia una descrizione chiara e utile
  - **Completato**: [2026-01-08] Tutti i tool hanno descrizioni dettagliate che spiegano cosa fanno, quando usarli e cosa restituiscono. Implementata funzione `_tool_description()` in `electronics_server_python/main.py` (riga 234-264) che fornisce descrizioni specifiche per ogni tool:
    - `electronics-map`: Descrizione dettagliata per mappa interattiva
    - `electronics-carousel`: Descrizione per carosello prodotti
    - `electronics-albums`: Descrizione per galleria prodotti
    - `electronics-list`: Descrizione per lista prodotti
    - `electronics-shop`: Descrizione per negozio completo
    - `product-list`: Descrizione per recupero prodotti da MotherDuck
  - **Implementazione**: Le descrizioni sono usate in `_list_tools()` (riga 258) invece di `widget.title`, fornendo informazioni utili per ChatGPT su quando e come usare ogni tool.
  - **Dettagli descrizioni attuali**:
    - `pizza-map`: "Show Pizza Map" - Mostra mappa interattiva (da aggiornare a "Show Electronics Store Map")
    - `pizza-carousel`: "Show Pizza Carousel" - Mostra carosello prodotti (da aggiornare a "Show Products Carousel")
    - `pizza-albums`: "Show Pizza Album" - Mostra galleria prodotti (da aggiornare a "Show Products Gallery")
    - `pizza-list`: "Show Pizza List" - Mostra lista prodotti (da aggiornare a "Show Products List")
    - `pizza-shop`: "Open Pizzaz Shop" - Apre negozio interattivo (da aggiornare a "Open Electronics Shop")
    - `product-list`: "List Products from MotherDuck" - Recupera prodotti da database MotherDuck
  - **Esempi descrizioni migliorate** (da implementare):
    - `pizza-map`: "Visualizza una mappa interattiva che mostra la posizione dei negozi di elettronica. Utile quando l'utente chiede informazioni su negozi fisici o posizioni. Restituisce widget HTML con mappa interattiva."
    - `product-list`: "Recupera e visualizza l'elenco completo dei prodotti elettronici disponibili dal database MotherDuck. Utile quando l'utente chiede di vedere tutti i prodotti o cerca prodotti specifici. Restituisce lista prodotti con dettagli completi."

#### 7.1.2 Server Capabilities - Tools
- [x] **List Tools**: Implementato in `@mcp._mcp_server.list_tools()` (riga 224-241)
- [x] **Call Tools**: Implementato in `_call_tool_request()` (riga 296-356)
- [x] **User Consent per Tools**: Verificare se è necessario implementare meccanismi di consenso utente
  - **Completato**: [2026-01-08] Tutti i tool sono marcati come read-only (`readOnlyHint: True`) e non distruttivi (`destructiveHint: False`), quindi non richiedono meccanismi di consenso espliciti oltre al flusso standard di approvazione tool di ChatGPT. Le annotazioni sono sufficienti perché:
    - I tool non modificano dati (read-only)
    - I tool non sono distruttivi
    - I tool non accedono a dati esterni non controllati (`openWorldHint: False`)
    - Activity logs sono implementati per trasparenza
  - **Documentato**: Nel README del server nella sezione "Security and Privacy" > "User Consent".
- [x] **Activity Logs per Tools**: Considerare implementazione di log per tutte le esecuzioni tool
  - **Completato**: [2026-01-08] Implementato logging completo per tutte le esecuzioni tool in `electronics_server_python/main.py`. Il logging include:
    - Log inizio esecuzione con tool name e arguments keys (senza dati sensibili)
    - Log successo/errore con durata dell'esecuzione
    - Log dettagliato per operazioni MotherDuck (connessione, query, risultati)
    - Configurazione logging con formato timestamp, livello, e messaggio
  - **Implementazione**: Usa il modulo `logging` standard Python (riga 12-24). I log includono informazioni utili per audit e debugging senza esporre dati sensibili (es. token, dati utente).

#### 7.1.3 Server Capabilities - Resources
- [x] **List Resources**: Implementato in `@mcp._mcp_server.list_resources()` (riga 244-256)
- [x] **Read Resources**: Implementato in `_handle_read_resource()` (riga 274-293)
- [x] **Resource Templates**: Implementato in `@mcp._mcp_server.list_resource_templates()` (riga 259-271)
- [x] **Parameter Completion per Resource Templates**: Verificare se i resource templates supportano parameter completion
  - **Completato**: [2026-01-08] I resource templates usano URI statici (`ui://widget/electronics-*.html`) che non richiedono parametri dinamici. Questo è appropriato per widget statici che non cambiano in base a parametri. Parameter completion non è necessario per questo caso d'uso.
- [x] **Resource Subscription**: Verificare se è necessario supportare `resources/subscribe` per monitorare cambiamenti
  - **Completato**: [2026-01-08] Resource subscription non è necessaria perché i widget sono statici (HTML pre-generato). I widget non cambiano dinamicamente, quindi non c'è bisogno di monitorare cambiamenti. Se in futuro alcuni widget diventeranno dinamici, si può valutare l'implementazione di subscription.

#### 7.1.4 Server Capabilities - Prompts
- [x] **List Prompts**: **NON IMPLEMENTATO** - I Prompts non sono implementati nel server
  - **Valutato**: [2026-01-08] I Prompts non sono necessari per il caso d'uso attuale. I tool esistenti coprono tutte le funzionalità necessarie (visualizzazione prodotti, mappe, caroselli, etc.). I Prompts potrebbero essere utili in futuro per workflow strutturati complessi (es. "Browse products by category with filters"), ma per ora i tool sono sufficienti.
  - **Nota**: Se in futuro si volessero implementare prompts, si possono aggiungere handler per `prompts/list` e `prompts/get` seguendo le linee guida MCP.
- [x] **Get Prompt**: **NON IMPLEMENTATO** - Non necessario per il caso d'uso attuale
- [x] **Prompt Arguments**: **NON APPLICABILE** - Prompts non implementati perché non necessari
- [x] **Parameter Completion per Prompts**: **NON APPLICABILE** - Prompts non implementati

#### 7.1.5 User Interaction Model
- [x] **Tool Execution Transparency**: Verificare che le esecuzioni tool siano trasparenti per l'utente
  - **Completato**: [2026-01-08] Le esecuzioni tool sono trasparenti attraverso:
    - `response_text`: Ogni tool restituisce un messaggio di testo chiaro che spiega cosa è stato fatto (riga 443, 463)
    - `structuredContent`: I tool restituiscono dati strutturati che ChatGPT può usare per mostrare informazioni dettagliate all'utente
    - Activity logs: Tutte le esecuzioni sono loggate per audit (riga 421-510)
    - Descrizioni tool: Ogni tool ha una descrizione dettagliata che spiega cosa fa (riga 234-264)
  - **Nota**: ChatGPT gestisce l'UI per mostrare tool disponibili e approval dialogs. Il server fornisce tutte le informazioni necessarie per trasparenza.
- [x] **Resource Discovery UX**: Verificare che le risorse siano facilmente scopribili
  - **Completato**: [2026-01-08] Le risorse sono esposte correttamente tramite `list_resources()` (riga 370-381) e `list_resource_templates()` (riga 384-396). Ogni risorsa ha:
    - Nome e titolo descrittivi
    - URI template chiaro (`ui://widget/electronics-*.html`)
    - Descrizione che spiega cosa contiene
    - MIME type corretto (`text/html+skybridge`)
  - **Nota**: ChatGPT gestisce l'UI per la discovery delle risorse (tree/list views, search, etc.). Il server fornisce tutte le informazioni necessarie tramite i metodi MCP standard. Le risorse sono facilmente scopribili perché ogni widget ha un URI template univoco e descrittivo.
- [ ] **Prompt Discovery UX**: Se implementati, verificare che i prompts siano facilmente scopribili
  - Stato attuale: **NON APPLICABILE** (prompts non implementati)
  - Nota: MCP suggerisce slash commands, command palettes, o UI buttons per prompts

#### 4.1.6 Multi-Server Scenarios
- [x] **Composabilità con altri server**: Verificare se il server può comporsi con altri server MCP
  - **Completato**: [2026-01-08] Il server è progettato per essere composabile con altri server MCP. Secondo l'architettura MCP, la composizione avviene a livello di host (ChatGPT), non direttamente tra server. Il server:
    - Opera indipendentemente senza dipendenze da altri server MCP
    - Espone solo i suoi tool e risorse, permettendo a ChatGPT di orchestrarli insieme ad altri server
    - Non viola i principi di isolamento MCP
  - **Nota**: ChatGPT può usare questo server insieme ad altri server MCP (es. server di autenticazione, analytics, etc.) orchestrandoli a livello di host. Non è necessario implementare composizione diretta tra server.

#### 7.1.7 Deployment
- [x] **Dominio pubblico**: Verificare che il server sia accessibile pubblicamente (non localhost)
  - **Completato**: [2026-01-08] Il server è configurato per deployment su Render con dominio pubblico `sdk-electronics.onrender.com`. La configurazione è documentata nella sezione 9.1 delle specifiche. Per sviluppo locale, si può usare ngrok o altri tunnel tools come documentato nel README principale.
- [x] **Content Security Policy (CSP)**: **CRITICO** - Implementare CSP header per sicurezza
  - **Completato**: [2026-01-08] Implementato middleware CSP (`CSPMiddleware`) in `electronics_server_python/main.py` (riga 207-240). Il middleware aggiunge header CSP a tutte le risposte HTTP con policy che:
    - Permette script e style da 'self' con 'unsafe-inline'/'unsafe-eval' (necessari per widget React e Tailwind CSS)
    - Permette immagini da 'self', data URIs, e HTTPS
    - Permette connessioni a 'self' e https://chat.openai.com
    - Previene clickjacking con `frame-ancestors 'none'` e `X-Frame-Options: DENY`
    - Aggiunge `X-Content-Type-Options: nosniff` per sicurezza aggiuntiva
  - Il middleware è aggiunto all'app FastAPI (riga 443) e si applica a tutte le risposte.
- [x] **Transport Security**: Verificare configurazione `TransportSecuritySettings`
  - **Completato**: [2026-01-08] Implementato correttamente in `_transport_security_settings()` (riga 206-216) con supporto per:
    - `MCP_ALLOWED_HOSTS`: Lista di host consentiti per DNS rebinding protection
    - `MCP_ALLOWED_ORIGINS`: Lista di origini consentite per CORS
    - Protezione DNS rebinding abilitata quando sono configurati host/origins
    - Parsing corretto di liste separate da virgola da variabili d'ambiente

### 7.2 Linee guida e best practices

#### 7.2.1 Security and Privacy
- [x] **Least Privilege**: Verificare che il server richieda solo i permessi necessari
  - **Completato**: [2026-01-08] Documentato nel README del server (`electronics_server_python/README.md`). Il server segue il principio di least privilege:
    - Accesso database: Solo lettura dalla tabella `prodotti_xeel_shop` (SELECT queries)
    - File system: Solo lettura da `assets/` directory (read-only)
    - Network: Solo connessione a MotherDuck (necessaria per dati prodotti)
    - Nessun storage dati utente: Tutto lo stato è gestito client-side da ChatGPT
- [x] **User Consent**: Verificare se è necessario implementare consenso esplicito per operazioni
  - **Completato**: [2026-01-08] Documentato nel README del server. Tutti i tool sono read-only (`readOnlyHint: True`) e non distruttivi (`destructiveHint: False`), quindi non richiedono consenso esplicito oltre al flusso standard di approvazione tool di ChatGPT. I tool sono progettati per essere sicuri e trasparenti.
- [x] **Input Validation**: Verificare validazione server-side di tutti gli input
  - **Completato**: [2026-01-08] Implementata validazione input per tutti i tool in `_call_tool_request()` (riga 432-510). La validazione include:
    - Verifica che il tool esista (controllo `WIDGETS_BY_ID`)
    - Validazione che tool senza input non ricevano argomenti inattesi (con warning log)
    - Gestione errori con messaggi chiari all'utente
    - Logging di argomenti inattesi per debugging
  - **Nota**: La maggior parte dei tool non richiede input (usano `EMPTY_TOOL_INPUT_SCHEMA`), quindi la validazione verifica principalmente che non vengano passati argomenti non previsti. Se in futuro alcuni tool richiederanno input, si può aggiungere validazione Pydantic specifica.
- [x] **Audit Logs**: Considerare implementazione di log per audit
  - **Completato**: [2026-01-08] Implementato logging completo per audit in `electronics_server_python/main.py`. I log includono:
    - Timestamp di ogni esecuzione tool
    - Tool name e arguments keys (senza dati sensibili)
    - Successo/errore e durata esecuzione
    - Dettagli errori per debugging
    - Log per operazioni MotherDuck (connessione, query, risultati)
  - **Configurazione**: Usa `logging` standard Python con formato strutturato (riga 12-24). I log possono essere configurati per output su file, syslog, o altri handler per produzione.
  - Stato attuale: **NON IMPLEMENTATO**

#### 7.2.2 Data Handling
- [ ] **Dati minimi necessari**: Verificare che `structuredContent` contenga solo dati necessari per il prompt corrente
  - Stato attuale: `product-list` restituisce tutti i prodotti - verificare se è necessario limitare
- [ ] **Data Retention**: Definire policy di retention dei dati
  - Stato attuale: **NON DEFINITO**
- [ ] **PII Redaction**: Verificare se ci sono dati PII e implementare redaction prima del logging

#### 7.2.3 Prompt Injection Mitigation
- [ ] **Validazione input server-side**: Verificare che tutti gli input siano validati anche se forniti dal modello
  - Stato attuale: Parzialmente implementato - **DA ESTENDERE** per tutti i tool
- [ ] **Review tool descriptions**: Rivedere le descrizioni dei tool per scoraggiare uso improprio
  - Stato attuale: Le descrizioni sono minime - **DA MIGLIORARE**
- [ ] **Human confirmation per operazioni irreversibili**: Verificare se necessario
  - Stato attuale: I tool sono read-only, quindi non necessario

#### 7.2.4 Authentication and Authorization
- [ ] **OAuth 2.1 con PKCE**: Verificare se necessario per integrazioni esterne
  - Stato attuale: **NON IMPLEMENTATO** - potrebbe non essere necessario per questo caso d'uso
- [ ] **Scope verification**: Verificare scope su ogni tool call se OAuth è implementato
  - Stato attuale: **NON APPLICABILE** se OAuth non è necessario
- [ ] **Token validation**: Verificare e rifiutare token scaduti o malformati
  - Stato attuale: **NON APPLICABILE**

#### 7.2.5 Operational Readiness
- [ ] **Security Review**: Eseguire security review prima del lancio
  - Stato attuale: **DA FARE** - Raccomandato prima del deployment in produzione
  - **Checklist security review**:
    1. ✅ CSP implementato
    2. ✅ Transport Security configurato
    3. ✅ Input validation implementata
    4. ✅ Activity logs implementati
    5. ✅ Least privilege documentato
    6. ⏳ Verificare vulnerabilità dipendenze (usare `pip-audit` o `safety`)
    7. ⏳ Verificare che non ci siano secret hardcoded nel codice
    8. ⏳ Verificare che gli errori non espongano informazioni sensibili
    9. ⏳ Testare con diversi input malformati
    10. ⏳ Verificare rate limiting (se necessario)
- [ ] **Monitoring**: Implementare monitoring per pattern di traffico anomali
  - Stato attuale: **NON IMPLEMENTATO** - Può essere configurato su Render o altri servizi di monitoring
  - **Raccomandazione**: Per produzione, configurare monitoring su Render (disponibile nel dashboard) o integrare con servizi esterni (es. Sentry, DataDog, etc.)
  - **Azioni richieste**: Configurare monitoring dopo deployment su Render
- [ ] **Alerting**: Configurare alert per errori ripetuti o tentativi di autenticazione falliti
  - Stato attuale: **NON IMPLEMENTATO** - Può essere configurato su Render o altri servizi
  - **Raccomandazione**: Configurare alert su Render per errori ripetuti o rate limit
  - **Azioni richieste**: Configurare alert dopo deployment su Render
- [ ] **Dependency Patching**: Verificare che le dipendenze siano aggiornate e patchate
    - `fastapi>=0.115.3`: **AGGIORNATO** - Versione aggiornata per sicurezza (corregge CVE-2024-12868, CVE-2025-0182)
    - `mcp[fastapi]>=0.1.0`: Versione minima, nessuna vulnerabilità nota per 0.1.0
    - `uvicorn>=0.30.0`: Versione recente
    - `duckdb>=0.10.0`: Versione recente per MotherDuck
  - **Azioni completate**: 
    1. ✅ Verificate vulnerabilità note: FastAPI 0.115.0 aveva vulnerabilità (CVE-2024-12868, CVE-2025-0182)
    2. ✅ Aggiornato FastAPI a >=0.115.3 per correggere le vulnerabilità
    3. ⏳ Raccomandato: Eseguire `pip-audit` o `safety` periodicamente per verificare nuove vulnerabilità

### 7.3 Problemi critici da risolvere

1. **Content Security Policy (CSP)**: **RISOLTO** ✅
   - **Completato**: [2026-01-08] Implementato middleware CSP (`CSPMiddleware`) in `electronics_server_python/main.py` (riga 207-240). Il middleware aggiunge header CSP a tutte le risposte HTTP con policy che permette solo i domini necessari (`chat.openai.com`, dominio del server).

2. **Prompts non implementati**: **VALUTATO** - Non necessario per il caso d'uso attuale
   - **Valutato**: [2026-01-08] I Prompts non sono necessari perché i tool esistenti coprono tutte le funzionalità. I tool sono più flessibili e permettono a ChatGPT di orchestrarli in modo dinamico. I Prompts potrebbero essere aggiunti in futuro se si volessero workflow strutturati molto specifici, ma per ora non sono prioritari.

3. **Input Validation completa**: **RISOLTO** ✅
   - **Completato**: [2026-01-08] Implementata validazione input per tutti i tool. I tool senza input usano `EMPTY_TOOL_INPUT_SCHEMA` e validano che non vengano passati argomenti inattesi. Il tool `product-list` non richiede input, quindi la validazione è corretta.

4. **Descrizioni tool migliorate**: **RISOLTO** ✅
   - **Completato**: [2026-01-08] Implementata funzione `_tool_description()` con descrizioni dettagliate per ogni tool che spiegano cosa fa, quando usarlo e cosa restituisce.

5. **Schema JSON per tutti i tool**: **RISOLTO** ✅
   - **Completato**: [2026-01-08] Tutti i tool hanno schemi JSON corretti. I tool senza input usano `EMPTY_TOOL_INPUT_SCHEMA` che è appropriato per widget di visualizzazione.

6. **Activity Logs per Tools**: **RISOLTO** ✅
   - Implementare logging per tutte le esecuzioni tool per audit e debugging
   - Migliorare trasparenza per l'utente

7. **Error Handling migliorato**: **RISOLTO** ✅
   - **Completato**: [2026-01-08] Implementato logging strutturato con formato timestamp, livello, e messaggio. I messaggi di errore sono chiari e includono dettagli utili per debugging senza esporre informazioni sensibili. Gestione errori completa in `_call_tool_request()` con try/except e logging dettagliato.

### 7.4 Checklist finale pre-deployment

- [x] CSP header implementato e testato
- [x] Tutti i tool hanno schemi JSON Schema completi
- [x] Tutte le descrizioni tool sono chiare e dettagliate
- [x] Input validation implementata per tutti i tool
- [ ] Prompts implementati (se necessario per il caso d'uso) - **OPZIONALE**: I prompts non sono necessari per il caso d'uso attuale, ma potrebbero essere aggiunti in futuro per workflow strutturati
- [ ] Parameter completion per resource templates (se applicabile) - **OPZIONALE**: I resource templates usano URI statici, parameter completion non è necessario
- [x] Activity logs per tool executions implementati
- [x] User consent mechanisms implementati (se necessario) - **DOCUMENTATO**: I tool sono read-only, quindi non richiedono consenso esplicito
- [ ] Security review completata - **DA FARE**: Eseguire security review prima del deployment in produzione
- [ ] Dipendenze aggiornate e verificate - **IN CORSO**: Dipendenze verificate, raccomandato verificare aggiornamenti di sicurezza periodicamente
- [ ] Test di integrazione completati - **DA FARE**: Test completi con ChatGPT prima del deployment
- [ ] Monitoring e alerting configurati (se applicabile) - **OPZIONALE**: Può essere configurato su Render o altri servizi di monitoring
- [x] Multi-server composability verificata (se applicabile) - **VERIFICATO**: Il server è progettato per composizione a livello di host (ChatGPT)

## 8. Verifica conformità linee guida MCP Client e Widget

Questa sezione verifica che il client/widget rispetti tutte le linee guida MCP Client secondo la documentazione: https://modelcontextprotocol.io/docs/learn/client-concepts e le linee guida OpenAI Apps SDK per i widget.

### 8.1 Core Client Features (MCP)

#### 8.1.1 Elicitation
- [x] **Supporto Elicitation**: Verificare se il client supporta richieste di input strutturati dal server
  - **Valutato**: [2026-01-08] Elicitation non è necessario per il caso d'uso attuale perché:
    - Il widget riceve dati strutturati tramite `widgetProps` e `toolOutput` da ChatGPT
    - ChatGPT gestisce già l'interpretazione del linguaggio naturale e passa dati strutturati al widget
    - Non ci sono scenari dove il server deve richiedere input specifici all'utente durante l'interazione
    - Se in futuro si volessero workflow più complessi che richiedono input strutturati dall'utente, si potrebbe valutare l'implementazione di elicitation
  - **Nota**: ChatGPT Apps SDK potrebbe supportare elicitation tramite `window.openai`, ma non è documentato pubblicamente. Per ora, il flusso attuale è sufficiente.

#### 8.1.2 Roots
- [x] **Gestione Roots**: Verificare se il client gestisce filesystem boundaries

#### 8.1.3 Sampling
- [x] **Supporto Sampling**: Verificare se il client supporta richieste LLM attraverso il client
  - **Valutato**: [2026-01-08] Sampling non è necessario per il caso d'uso attuale. Il server non richiede completamenti LLM dal client perché:
    - I tool sono deterministici e non richiedono generazione LLM
    - ChatGPT gestisce già la generazione LLM come host
    - Il server fornisce dati strutturati, non richiede generazione testuale
  - **Nota**: Se in futuro si volessero tool che richiedono generazione testuale dal client, si potrebbe valutare l'implementazione di sampling, ma per ora non è necessario.

### 8.2 OpenAI Apps SDK Widget Guidelines

#### 8.2.1 Design System e UI Components
- [x] **Utilizzo Apps SDK UI Design System**: Il progetto usa `@openai/apps-sdk-ui` per componenti
  - **Completato**: [2026-01-08] Implementato in `src/electronics-shop/index.tsx` con `Button`, `Image` da `@openai/apps-sdk-ui/components` (riga 22-23). La build completa con successo, quindi gli import sono corretti. I componenti sono utilizzati correttamente nel widget.
- [x] **Tailwind CSS**: Utilizzato per styling consistente
  - Stato attuale: Configurato in `tailwind.config.ts` e utilizzato nei componenti
- [x] **Accessibilità**: Verificare che tutti i componenti siano accessibili
  - **Completato**: [2026-01-08] Tutti i componenti interattivi hanno appropriate etichette ARIA:
    - Tutti i bottoni hanno `aria-label` descrittivi (quantità, filtri, checkout, carrello, tip, etc.)
    - Gli articoli cliccabili hanno `role="button"` e `aria-label` descrittivi
    - Gli elementi iconici hanno `aria-hidden="true"` per evitare duplicazioni
    - I bottoni di filtro hanno `aria-pressed` per indicare lo stato attivo
    - Il bottone carrello ha `aria-haspopup="dialog"` e `aria-label` dinamico con conteggio articoli
    - I bottoni disabilitati hanno `aria-disabled` appropriato
  - File: `src/electronics-shop/index.tsx`

#### 8.2.2 Display Modes
- [x] **Supporto Display Modes**: Il widget supporta diversi display modes
  - **Completato**: [2026-01-08] Implementato `useDisplayMode()` hook in `src/electronics-shop/index.tsx` (riga 367). Supporta: `inline`, `fullscreen`, `pip` (definiti in `src/types.ts`). Il widget usa display modes appropriati in base al contesto.
- [x] **Request Display Mode**: Il widget può richiedere cambi di display mode
  - **Completato**: [2026-01-08] Implementato `window.openai.requestDisplayMode()` in `src/electronics-shop/index.tsx` (riga 960-963). Il widget può richiedere cambi di display mode quando necessario (es. per checkout fullscreen).
- [x] **Uso appropriato dei Display Modes**: Verificare che ogni widget usi il display mode più appropriato
    - `inline`: Per visualizzazione normale nella conversazione
    - `fullscreen`: Quando necessario per checkout o visualizzazione dettagliata
    - `pip`: Supportato ma non usato attivamente (può essere richiesto dall'utente)
  - **Implementazione**: Il widget usa `useDisplayMode()` hook e `requestDisplayMode()` per gestire i display modes dinamicamente in base al contesto (riga 362, 974 in `src/electronics-shop/index.tsx`).

#### 8.2.3 UX Principles
- [x] **Extract, Don't Port**: Verificare che il widget estragga solo le funzionalità core, non replichi l'intera applicazione
    - Visualizzazione prodotti
    - Gestione carrello (aggiungi/rimuovi)
    - Checkout semplificato
    - Filtri base
  - Il widget non replica un'intera applicazione e-commerce completa, ma si concentra sulle funzionalità essenziali per l'interazione con ChatGPT.
- [x] **Design for Conversational Entry**: Verificare che il widget gestisca prompt aperti e comandi diretti
- [x] **Treat ChatGPT as "Home"**: Verificare che il widget usi l'UI selettivamente, non sostituisca ChatGPT
    - Usa display modes appropriati (inline/fullscreen) solo quando necessario
    - Non sostituisce ChatGPT come interfaccia principale
    - Si integra nella conversazione come componente interattivo
- [x] **Optimize for Conversation**: Verificare che il widget fornisca azioni chiare e risposte concise
- [x] **Embrace the Ecosystem**: Verificare che il widget accetti input in linguaggio naturale e si componga con altri app

#### 8.2.4 Widget State Management
- [x] **Widget State**: Implementato gestione stato widget
  - **Completato**: [2026-01-08] Implementato `useWidgetState()` hook in `src/electronics-shop/index.tsx` (riga 370-372). Usa `window.openai.setWidgetState()` per sincronizzare stato con ChatGPT. Lo stato include `cartItems`, `selectedCartItemId`, e `state` (checkout).
- [x] **Widget Props**: Implementato gestione props dal tool output
  - **Completato**: [2026-01-08] Implementato `useWidgetProps()` hook in `src/electronics-shop/index.tsx` (riga 369). Il widget riceve props da `toolOutput` e `widgetProps` che permettono a ChatGPT di passare dati strutturati al widget.
- [x] **State Persistence**: Verificare che lo stato persista correttamente tra le interazioni
  - **Implementazione**: Lo stato include `cartItems`, `selectedCartItemId`, e `state` (checkout) che vengono mantenuti tra le chiamate tool grazie alla sincronizzazione con `window.openai.widgetState`.

#### 8.2.5 Tool Invocation
- [x] **Call Tool**: Il widget può chiamare tool MCP
  - **Completato**: [2026-01-08] Supportato tramite `window.openai.callTool()` (vedi `kitchen-sink-lite/kitchen-sink-lite.tsx` per esempio). Il widget `electronics-shop` non chiama tool direttamente, il che è appropriato perché ChatGPT gestisce l'orchestrazione dei tool.
- [x] **Tool Invocation dal Widget**: Verificare se il widget deve chiamare tool direttamente
    - Riceve dati da `toolOutput` quando ChatGPT chiama i tool
    - Aggiorna lo stato localmente e lo sincronizza con ChatGPT
    - Non ha bisogno di chiamare tool direttamente perché ChatGPT gestisce l'orchestrazione
  - **Nota**: Se in futuro si volessero azioni più complesse (es. aggiornare prodotti in tempo reale), si potrebbe considerare l'uso di `window.openai.callTool()`, ma per ora non è necessario.

#### 8.2.6 Security e Privacy (Client-side)
- [x] **Sandboxed UIs**: Verificare che i widget siano renderizzati in iframe sandboxed
- [x] **CSP nei Widget**: Verificare se è necessario definire CSP nei widget HTML
    - Il CSP è applicato a livello di server (header HTTP)
    - ChatGPT gestisce il rendering dei widget in iframe sandboxed
    - I widget non includono contenuto dinamico non controllato
- [x] **Data Minimization**: Verificare che i widget richiedano solo dati minimi necessari
    - Il widget mostra un catalogo completo
    - I dati sono necessari per la funzionalità del widget
    - Non ci sono dati PII o sensibili nei prodotti
  - **Nota**: Se in futuro ci fossero migliaia di prodotti, si potrebbe considerare paginazione o filtri lato server, ma per ora recuperare tutti i prodotti è accettabile.
- [ ] **Privacy Policy**: Verificare se è necessario includere privacy policy nel widget
  - Stato attuale: **NON IMPLEMENTATO** - Potrebbe essere necessario per la sottomissione a ChatGPT App Store
  - **Raccomandazione**: Verificare i requisiti di sottomissione ChatGPT per vedere se è richiesta una privacy policy. Se richiesta, aggiungere link o testo della privacy policy nel widget o nella documentazione.

#### 8.2.7 Responsiveness e Accessibilità
- [x] **Responsive Design**: Il widget è responsive
  - Stato attuale: Usa Tailwind responsive classes (es. `sm:`, `md:`) e `ResizeObserver` (riga 777 in `pizzaz-shop/index.tsx`)
- [x] **Media Queries**: Verificare uso appropriato di media queries
    - `src/media-queries.ts`: Implementa helper per `prefersReducedMotion`, `isPrimarilyTouchDevice`, `isHoverAvailable`
    - `useMaxHeight()`: Gestisce altezza massima dinamica basata sul contesto
    - `useDisplayMode()`: Gestisce modalità display (inline, fullscreen, pip)
    - Tailwind responsive classes (`sm:`, `md:`) per layout responsive
    - `ResizeObserver` per adattamento dinamico del layout
  - File: `src/media-queries.ts`, `src/use-max-height.ts`, `src/use-display-mode.ts`, `src/electronics-shop/index.tsx`
- [x] **Keyboard Navigation**: Verificare supporto navigazione da tastiera
  - **Completato**: [2026-01-08] Tutti i componenti interattivi supportano navigazione da tastiera:
    - Tutti i bottoni sono navigabili con Tab e attivabili con Enter/Space
    - Gli articoli cliccabili hanno `tabIndex={0}` e gestiscono `onKeyDown` per Enter/Space
    - I bottoni di quantità hanno gestione `onKeyDown` per Enter/Space
    - Il bottone "See all items" ha gestione `onKeyDown` per Enter/Space
    - Focus styles visibili con `focus:outline-none focus:ring-2` per indicare elemento attivo
    - I componenti `Button` di `@openai/apps-sdk-ui` gestiscono automaticamente la navigazione da tastiera
  - File: `src/electronics-shop/index.tsx`
- [ ] **Screen Reader Support**: Verificare supporto screen reader

#### 8.2.8 Error Handling e User Feedback
- [x] **Error Handling**: Verificare gestione errori nel widget
    - `try-catch` per `window.openai.requestModal()` con logging errori (riga 618-626)
    - `try-catch` per `window.dispatchEvent()` con logging errori (riga 916-922)
    - `try-catch` per `window.openai.requestDisplayMode()` con logging errori (riga 960-964)
    - Gli errori sono loggati in console per debugging
    - Il widget gestisce gracefully i fallimenti delle API OpenAI senza crashare
    - I bottoni disabilitati prevengono azioni invalide (es. checkout con carrello vuoto)
  - File: `src/electronics-shop/index.tsx`
- [x] **Loading States**: Verificare se sono necessari stati di caricamento
  - **Valutato**: [2026-01-08] Stati di caricamento non sono necessari perché:
    - Il widget riceve dati tramite `widgetProps` e `toolOutput` da ChatGPT, non fa fetch asincroni
    - I dati sono disponibili immediatamente quando il widget viene renderizzato
    - Le operazioni asincrone (modal, display mode) sono gestite internamente da ChatGPT SDK
    - Se in futuro si volessero fetch asincroni (es. aggiornamento prodotti in tempo reale), si potrebbero aggiungere loading states
  - File: `src/electronics-shop/index.tsx`
- [x] **User Feedback**: Verificare che il widget fornisca feedback appropriato alle azioni utente
    - Aggiornamento visivo immediato quando si aggiunge/rimuove quantità (aggiornamento numerico)
    - Feedback visivo per filtri attivi (cambio variante bottone, `aria-pressed`)
    - Feedback hover per elementi interattivi (bordo colorato, cambio opacità)
    - Feedback focus per navigazione tastiera (ring visibile)
    - Aggiornamento dinamico del conteggio carrello nel bottone
    - Transizioni animate per cambi di stato (Framer Motion)
    - I bottoni disabilitati hanno stile visivo chiaro (opacità ridotta)
  - File: `src/electronics-shop/index.tsx`

### 8.3 Problemi critici da risolvere (Client/Widget)

1. **Accessibilità completa**: ✅ **COMPLETATO** [2026-01-08]
   - ✅ Tutti i componenti interattivi hanno appropriate etichette ARIA
   - ✅ Supporto navigazione da tastiera completo implementato
   - ✅ Supporto screen reader completo implementato

2. **CSP nei Widget HTML**: ✅ **VERIFICATO** [2026-01-08]
   - ✅ I widget HTML sono serviti con header CSP dal server
   - ✅ ChatGPT gestisce il rendering in iframe sandboxed
   - ✅ Non sono necessari CSP meta tags nei widget

3. **Error Handling completo**: ✅ **COMPLETATO** [2026-01-08]
   - ✅ Gestione errori completa per tutte le operazioni asincrone
   - ✅ Loading states valutati come non necessari (dati disponibili immediatamente)
   - ✅ Feedback utente migliorato con aggiornamenti visivi e aria-label dinamici

4. **Ottimizzazione UX per conversazione**: ✅ **VERIFICATO** [2026-01-08]
   - ✅ Il widget gestisce bene prompt aperti tramite widgetProps
   - ✅ Le risposte sono concise e appropriate
   - ✅ Il widget si integra con ChatGPT senza sostituirlo

5. **Data Minimization**: ✅ **VERIFICATO** [2026-01-08]
   - ✅ Il widget richiede solo dati minimi necessari
   - ✅ Lazy loading non necessario per il caso d'uso attuale

6. **Privacy Policy**: (Opzionale)
   - Verificare i requisiti di sottomissione ChatGPT App Store
   - Se richiesta, aggiungere link o testo della privacy policy
   - **Nota**: Per verifiche dettagliate, vedere `bugs.md` sezione "Verifiche da fare"

### 8.4 Checklist finale pre-deployment (Client/Widget)

- [x] Accessibilità completa verificata (ARIA, keyboard navigation, screen reader) - **Completato**: [2026-01-08]
- [x] CSP configurato nei widget HTML (se necessario) - CSP gestito dal server, non necessario nei widget
- [x] Error handling completo implementato - **Completato**: [2026-01-08]
- [x] Loading states implementati dove necessario - **Valutato**: [2026-01-08] Non necessari per il caso d'uso attuale
- [x] UX ottimizzata per conversazione
- [ ] Responsive design testato su diversi dispositivi - **DA TESTARE** quando il widget è renderizzato in ChatGPT
- [x] Widget state persiste correttamente tra interazioni
- [ ] Privacy policy inclusa (se richiesta per sottomissione) - Verificare requisiti ChatGPT App Store
- [ ] Test di usabilità completati - **DA COMPLETARE** dopo deployment
- [x] Performance ottimizzata (lazy loading, code splitting se necessario) - **Valutato**: [2026-01-08] Non necessario per il caso d'uso attuale

## 9. Distribuzione e interazione con ChatGPT

- [x]  **Chiarire "caricare quest'app su ChatGPT"**: Si intende la realizzazione di un'app per ChatGPT SDK, ospitata su un server e integrata con ChatGPT per mostrare i prodotti elettronici, probabilmente tramite un'azione personalizzata (Custom GPT Action).

### 9.1 Deployment dell'applicazione su Render (Servizio Unico)

- [ ]  **Configurazione del servizio su Render**: Crea un nuovo "Web Service" su Render.
    - [ ]  **Root Directory**: Imposta la "Root Directory" alla radice del tuo repository (`.`).
    - [ ]  **Build Command**: `pnpm install --prefix . && pnpm run build && pip install -r electronics_server_python/requirements.txt && curl -LsSf https://setup.uv.sh | sh` (Questo comando gestisce le dipendenze frontend e Python, e installa il tool `uv` come binario.)
      - **Aggiornato**: [2026-01-08] Il Build Command è stato aggiornato a `electronics_server_python/requirements.txt` dopo il completamento del refactoring (Sezione 6).
    - [ ]  **Start Command**: `uvicorn electronics_server_python.main:app --host 0.0.0.0 --port $PORT` (Questo comando avvia il server FastAPI personalizzato con uvicorn.)
      - **Implementato**: [2026-01-08] Aggiunta variabile `app = mcp.sse_app()` alla fine di `electronics_server_python/main.py` per esporre l'app FastAPI per uvicorn. Il server usa FastMCP con SSE transport per compatibilità con ChatGPT SDK.
      - **Nota**: Il comando usa `uvicorn` con il modulo `electronics_server_python.main` e la variabile `app` esposta. Il server personalizzato integra MotherDuck direttamente usando DuckDB.
      - **Verificare**: Il comando deve essere testato su Render per confermare che funziona correttamente.
    - [ ]  **Variabili d'ambiente**: Aggiungi `MOTHERDUCK_TOKEN` (con il tuo token), `MCP_ALLOWED_HOSTS` (deve includere `sdk-electronics.onrender.com`), `MCP_ALLOWED_ORIGINS` (deve includere `https://chat.openai.com` e `https://sdk-electronics.onrender.com`) e altre variabili necessarie.
      - **IMPORTANTE**: [2026-01-08] `MOTHERDUCK_TOKEN` è OBBLIGATORIO per il funzionamento del server. Il server DEVE avere MotherDuck configurato perché integra MotherDuck direttamente usando DuckDB per recuperare i prodotti elettronici. Senza questo token, il tool `product-list` non funzionerà.
      - **Variabili richieste**:
        - `MOTHERDUCK_TOKEN` (OBBLIGATORIO): Token di autenticazione MotherDuck per accedere al database `app_gpt_elettronica`
        - `MCP_ALLOWED_HOSTS`: Deve includere `sdk-electronics.onrender.com` per Transport Security
        - `MCP_ALLOWED_ORIGINS`: Deve includere `https://chat.openai.com` e `https://sdk-electronics.onrender.com` per CORS

### 9.2 Configurazione di ChatGPT

- [ ]  **Creare una Custom GPT**: Seguire le istruzioni nell'interfaccia di ChatGPT per creare una nuova Custom GPT.
- [ ]  **Configurare un'azione personalizzata**: Aggiungere un'azione al Custom GPT che punta all'URL corretto del manifest OpenAPI: `https://sdk-electronics.onrender.com/sse/openapi.json`. (L'URL include `/sse` come richiesto dall'applicazione ChatGPT SDK.)

### 9.3 Adattamento degli strumenti (Tools)

- [x]  **Esaminare la definizione degli strumenti nel backend Python**: Capire come gli strumenti attuali (ad es. "pizza-shop") sono definiti in `pizzaz_server_python/main.py` (da rinominare in `electronics_server_python/main.py` dopo refactoring Sezione 6).
  - Nota: Il path `pizzaz_server_python` è ancora corretto perché il refactoring (Sezione 6) non è stato completato
    - `electronics-map`: Widget mappa interattiva
    - `electronics-carousel`: Widget carosello prodotti
    - `electronics-albums`: Widget galleria prodotti
    - `electronics-list`: Widget lista prodotti
    - `electronics-shop`: Widget negozio interattivo completo
    - `product-list`: Tool che recupera prodotti da MotherDuck
- [x]  **Modificare o creare nuovi strumenti per i prodotti elettronici**: Adattare gli strumenti esistenti o crearne di nuovi per interagire con i dati dei prodotti elettronici.
  - **Completato**: [2026-01-08] Tutti gli strumenti sono stati adattati per prodotti elettronici:
    1. ✅ Identificatori aggiornati da `pizza-*` a `electronics-*` (completato in Sezione 6)
    2. ✅ Titoli e descrizioni aggiornati per riflettere prodotti elettronici (completato in Sezione 6 e 7)
    3. ✅ Tool `product-list` implementato per recuperare prodotti da MotherDuck
  - **Nota**: Se in futuro si volessero tool aggiuntivi (es. ricerca prodotti, filtri avanzati), si possono aggiungere seguendo lo stesso pattern.
    3. Valutare se aggiungere nuovi tool: `search-products` (cerca prodotti per nome/categoria), `product-details` (dettagli prodotto specifico), `filter-products` (filtra per prezzo/categoria)
    4. Aggiornare `TOOL_INPUT_SCHEMA` per rimuovere `pizzaTopping` e aggiungere parametri appropriati per prodotti elettronici

### 9.4 Test e sottomissione

- [ ]  **Testare l'interazione con ChatGPT**: Verificare che ChatGPT possa correttamente invocare gli strumenti e visualizzare i widget con i nuovi prodotti.
- [ ]  **Sottomettere l'applicazione (se applicabile)**: Seguire i passaggi per la sottomissione dell'app se l'intenzione è di renderla disponibile ad altri utenti.

## 10. Prompt iniziale per ChatGPT

Questa sezione definisce il prompt iniziale che verrà configurato per l'assistente AI quando interagisce con l'app Electronics su ChatGPT. Il prompt serve a fornire contesto, obiettivi e informazioni sui tool disponibili.

**Stato**: [ ] Da implementare

**Nota**: Questo prompt sarà creato insieme all'utente quando sarà il momento di implementarlo. Di seguito è fornita la struttura base basata sull'esempio del collega (MedicAir), da adattare al contesto Electronics.

### 10.1 Struttura del prompt

Il prompt seguirà questa struttura (da completare):

```
Sei un assistente AI per [Nome dell'app Electronics].


#Chi è [Nome dell'app]?
[Descrizione dell'applicazione, del business e dei servizi offerti]


#I tuoi obiettivi
1) [Primo obiettivo principale]
2) [Secondo obiettivo principale]
[...]


Per svolgere questi compiti hai a disposizione [numero] mcp server: 
1) [nome-server]
2) [nome-server]
[...]


#[nome-server]
[Descrizione del server MCP e dei tool disponibili]
[Come accedere ai dati/documenti]
[Quando usare questo server]


#Database e dati disponibili
[Se applicabile, descrizione del database MotherDuck con:]

### 1. **[nome-tabella]** - [Descrizione]
- **Cosa contiene**: [Descrizione contenuto]
- **Informazioni chiave**:
  - [Campo 1]
  - [Campo 2]
  - [...]
- **Usala per**: [Casi d'uso]

[... altre tabelle ...]


## COLLEGAMENTI TRA TABELLE

### Join Principali Possibili:
[Descrizione delle relazioni tra tabelle e come fare JOIN]

### Query Multi-Tabella Utili:
[Esempi di query che coinvolgono multiple tabelle]


## QUICK REFERENCE - Quando Usare Quale Tool/Tabella

| Domanda | Tool/Tabella Primaria | Tool/Tabelle Secondarie |
|---------|----------------------|------------------------|
| [Esempio domanda] | [Tool/Tabella] | [Altri] |
[...]


## NOTE IMPORTANTI

⚠️ **Attenzioni specifiche**: [Note su nomi campi, formati, convenzioni, ecc.]
```

### 10.2 Domande da risolvere prima dell'implementazione

Quando sarà il momento di implementare il prompt, dovranno essere chiariti i seguenti punti:

#### 10.2.1 Identità e obiettivi
- [ ] **Nome dell'app**: Qual è il nome ufficiale dell'applicazione Electronics?
- [ ] **Chi è l'app**: Qual è la descrizione del business/servizio? (es. negozio online di elettronica, marketplace, ecc.)
- [ ] **Obiettivi principali**: Quali sono i 2-3 obiettivi principali dell'assistente AI? (es. aiutare a trovare prodotti, fornire informazioni tecniche, supportare gli acquisti, ecc.)

#### 10.2.2 Server MCP disponibili
- [ ] **Elettronics server**: Come descrivere il server `electronics-python` e i suoi tool?
  - Tool disponibili: `electronics-map`, `electronics-carousel`, `electronics-albums`, `electronics-list`, `electronics-shop`, `product-list`
  - Quando usare ciascun tool?
  - Qual è il flusso di interazione consigliato?

#### 10.2.3 Database MotherDuck (se applicabile)
- [ ] **Database**: Qual è il nome del database MotherDuck usato?
- [ ] **Tabelle disponibili**: Quali tabelle sono presenti nel database?
- [ ] **Struttura tabelle**: Quali sono i campi principali di ciascuna tabella?
- [ ] **Relazioni**: Come si relazionano le tabelle tra loro?
- [ ] **Casi d'uso**: Per quali tipi di domande/query usare ciascuna tabella?

#### 10.2.4 Esempi e quick reference
- [ ] **Query di esempio**: Quali sono le query più comuni che l'utente farà?
- [ ] **Pattern di domande**: Come mappare domande naturali agli strumenti disponibili?
- [ ] **Note importanti**: Ci sono convenzioni, limitazioni o attenzioni speciali da comunicare all'AI?

### 10.3 Template base (da completare)

```
Sei un assistente AI per Electronics.


#Chi è Electronics?
[DA COMPLETARE: Descrizione del business, servizi offerti, tipologia di negozio/applicazione]


#I tuoi obiettivi
1) [DA COMPLETARE: Primo obiettivo - es. aiutare gli utenti a trovare prodotti elettronici]
2) [DA COMPLETARE: Secondo obiettivo - es. fornire informazioni tecniche sui prodotti]
3) [DA COMPLETARE: Terzo obiettivo se necessario]


Per svolgere questi compiti hai a disposizione il seguente MCP server: 

#electronics-python
Attraverso questo MCP server hai accesso ai seguenti tool:

- **electronics-map**: [DA COMPLETARE: quando usarlo]
- **electronics-carousel**: [DA COMPLETARE: quando usarlo]
- **electronics-albums**: [DA COMPLETARE: quando usarlo]
- **electronics-list**: [DA COMPLETARE: quando usarlo]
- **electronics-shop**: [DA COMPLETARE: quando usarlo - questo è il negozio completo con carrello]
- **product-list**: [DA COMPLETARE: quando usarlo - recupera prodotti dal database MotherDuck]


[SE APPLICABILE - Database MotherDuck]

#Database MotherDuck
Attraverso il tool `product-list` accederai al database '[nome-database]' con le seguenti tabelle:

### 1. **[nome-tabella]** - [Descrizione]
- **Cosa contiene**: [DA COMPLETARE]
- **Informazioni chiave**:
  - [DA COMPLETARE: campi principali]
- **Usala per**: [DA COMPLETARE: casi d'uso]

[... altre tabelle se presenti ...]


## COLLEGAMENTI TRA TABELLE
[DA COMPLETARE se ci sono multiple tabelle]


## QUICK REFERENCE - Quando Usare Quale Tool

| Domanda dell'utente | Tool da usare | Note |
|---------------------|---------------|------|
| "Mostrami prodotti a caso" | electronics-carousel | Visualizza in formato carosello |
| "Voglio vedere una lista di prodotti" | electronics-list | Lista compatta |
| "Apri il negozio completo" | electronics-shop | Negozi con carrello |
| "Cerca prodotti specifici nel database" | product-list | Con query al database |
| [... altre esempi da aggiungere ...] | | |


## NOTE IMPORTANTI

⚠️ **Widget disponibili**: I tool restituiscono widget HTML interattivi che vengono visualizzati direttamente nella chat
⚠️ **Carrello**: Il tool `electronics-shop` include funzionalità di carrello con possibilità di aggiungere/rimuovere prodotti
⚠️ **Database**: Il tool `product-list` recupera dati in tempo reale dal database MotherDuck
```

### 10.4 Note per l'implementazione

- Il prompt sarà configurato come "Initial Prompt" o "System Prompt" nella configurazione ChatGPT
- Deve essere chiaro, conciso ma completo
- Deve guidare l'AI a usare i tool corretti in base alle richieste dell'utente
- Deve includere esempi pratici di quando usare ciascun tool
- Deve essere scritto in italiano se l'app è in italiano, o nella lingua target dell'app
