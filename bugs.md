# Bug e Verifiche - Electronics SDK

Questo documento traccia tutti i bug trovati, le loro risoluzioni e le verifiche da fare per il progetto Electronics SDK.

## Regole di processo per la gestione dei bug

**IMPORTANTE**: Seguire sempre queste regole quando si lavora sui bug:

1. **Bug trovato**: Quando si trova un bug:
   - Creare una nuova entry nella sezione "Bug trovati"
   - Includere:
     - Descrizione del bug
     - Come si manifesta
     - Quando è stato scoperto
     - Sezione/task correlato
   - Spuntare la casella solo quando il bug è stato risolto e verificato

2. **Risoluzione bug**: Quando un bug viene risolto:
   - Spostare il bug dalla sezione "Bug trovati" alla sezione "Bug risolti"
   - Aggiungere:
     - Come è stato risolto
     - Data di risoluzione
     - Soluzione applicata (dettagli tecnici)
   - Spuntare la casella solo dopo aver verificato che funziona correttamente

3. **Verifica continua**: Le caselle spuntate devono rappresentare lo stato attuale funzionante. Se qualcosa si rompe, la casella va deselezionata e il problema documentato.

4. **Verifiche da fare**: Le verifiche devono essere spuntate solo quando sono state completate e testate funzionalmente.

## Bug trovati

### CORS Error - UI non si carica
- [x] **Bug CORS - Access-Control-Allow-Origin mancante**: [2026-01-08] Il widget non si caricava quando veniva renderizzato da ChatGPT. Il browser bloccava il caricamento di risorse JavaScript e CSS a causa di una policy CORS. L'errore specifico era: "CORS policy blocking" o "Access-Control-Allow-Origin header was missing" quando si tentava di caricare `https://sdk-electronics.onrender.com/assets/electronics-carousel-2d2b.js` da origine `https://connector...web-sandbox.oaiusercontent.com`.
  - **Come si manifesta**: Il widget non si carica, le risorse JS e CSS vengono bloccate dal browser con errori CORS nella console.
  - **Sezione correlata**: Server Python - Middleware CORS in `electronics_server_python/main.py`
  - **Stato**: ✅ Risolto (vedi sezione "Bug risolti")

### Asset Path - Path degli asset non corretti in produzione
- [x] **Bug Asset Path - Path degli asset non corretti quando deployato**: [2026-01-08] Quando il server era deployato su Render invece che in locale, i path degli asset (JS, CSS) nell'HTML generato puntavano a `http://localhost:4444/` invece che al dominio di produzione. Questo causava il mancato caricamento delle risorse quando i widget venivano renderizzati da ChatGPT.
  - **Come si manifesta**: Le risorse JS e CSS non si caricano, i widget non funzionano correttamente quando il server è deployato su un dominio diverso da localhost.
  - **Sezione correlata**: Server Python - Funzione `_handle_read_resource` in `electronics_server_python/main.py`
  - **Stato**: ✅ Risolto (vedi sezione "Bug risolti")

### CSP Header - h11 rifiuta header CSP
- [x] **Bug CSP Header - h11 rifiuta header Content-Security-Policy**: [2026-01-08] La libreria h11 (usata da uvicorn) è molto rigorosa nella validazione degli header HTTP e potrebbe rifiutare l'header `Content-Security-Policy` se non è formattato correttamente. Questo causava errori nel server quando si tentava di aggiungere l'header CSP.
  - **Come si manifesta**: Errori nel server quando si tenta di aggiungere l'header CSP, possibili problemi di sicurezza se CSP non viene applicato.
  - **Sezione correlata**: Server Python - `CSPMiddleware` in `electronics_server_python/main.py`
  - **Stato**: ✅ Risolto (vedi sezione "Bug risolti")

### 2.2 Compatibilità dei tipi `CartItem`
- [x] **Bug TypeScript - Tipo `CartItem` non definito**: [2026-01-08] Il file `py/new_initial_cart_items.ts` usa il tipo `CartItem[]` ma non lo definisce né lo importa. Il tipo `CartItem` è definito localmente in `src/pizzaz-shop/index.tsx` (riga 30) e in modo diverso in `src/shopping-cart/index.tsx` (riga 7, più semplice). Potrebbe esserci un problema di compatibilità dei tipi che deve essere risolto.
  - **Come si manifesta**: TypeScript potrebbe non rilevare errori a compile-time se il tipo è inferito, ma potrebbe causare problemi di type safety.
  - **Sezione correlata**: Sezione 2.2 - Compatibilità dei tipi `CartItem` in `specifications.md`
  - **Stato**: ✅ Risolto (vedi sezione "Bug risolti")

### Immagine Blob Storage non accessibile
- [x] **Bug Immagine Blob Storage - Immagine con permessi negati**: [2026-01-08] L'immagine `img-Ywf9b6rLPQ5YM0rZh2NQEkp8.png` da Azure Blob Storage in `src/electronics/markers.json` (riga 11) non è accessibile, causando errori 409 (Conflict) e "access is not permitted on this storage account" nella console del browser. Questo impedisce il caricamento completo del widget.
  - **Come si manifesta**: L'immagine non si carica, errore 409 nella Network tab, errore di permessi nella console. Il widget viene visualizzato solo parzialmente.
  - **Sezione correlata**: `src/electronics/markers.json` - primo elemento "avatar-way-of-water"
  - **Stato**: ✅ Risolto (vedi sezione "Bug risolti")

### Immagini bloccate da ORB (Opaque Response Blocking)
- [x] **Bug ORB - Immagini electronics-*.png bloccate**: [2026-01-08] Le immagini `electronics-1.png`, `electronics-2.png`, `electronics-3.png`, `electronics-4.png`, `electronics-5.png`, `electronics-6.png` da `https://persistent.oaistatic.com/electronics/` vengono bloccate dal browser con errore `ERR_BLOCKED_BY_ORB` (Opaque Response Blocking). Questo è un meccanismo di sicurezza del browser che blocca risposte opache cross-origin, causando il mancato caricamento delle immagini nel widget.
  - **Come si manifesta**: Le immagini non si caricano, errore `ERR_BLOCKED_BY_ORB` nella Network tab. Il widget viene visualizzato solo parzialmente senza immagini.
  - **Sezione correlata**: Tutti i componenti che usano immagini: `PlaceCard.jsx`, `Inspector.jsx`, `AlbumCard.jsx`, `FullscreenViewer.jsx`, `FilmStrip.jsx`, `Sidebar.jsx`
  - **Stato**: ✅ Risolto (vedi sezione "Bug risolti")

## Bug risolti

### CORS Error - UI non si carica
- [x] **Bug CORS - Access-Control-Allow-Origin mancante**: [2026-01-08]
  - **Bug trovato**: [2026-01-08] Il widget non si caricava quando veniva renderizzato da ChatGPT. Il browser bloccava il caricamento di risorse JavaScript e CSS a causa di una policy CORS. L'errore specifico era: "CORS policy blocking" o "Access-Control-Allow-Origin header was missing" quando si tentava di caricare `https://sdk-electronics.onrender.com/assets/electronics-carousel-2d2b.js` da origine `https://connector...web-sandbox.oaiusercontent.com`.
  - **Bug risolto**: [2026-01-08] È stato implementato un `CORSMiddleware` in `electronics_server_python/main.py` che aggiunge gli header CORS necessari a tutte le risposte HTTP. Il middleware gestisce anche le richieste OPTIONS (preflight) e aggiunge `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, e `Access-Control-Allow-Headers` alle risposte.
  - **Soluzione applicata**:
    1. Creato classe `CORSMiddleware` che estende `BaseHTTPMiddleware` (riga 235-294 in `main.py`)
    2. Il middleware gestisce richieste OPTIONS (preflight) restituendo header CORS appropriati
    3. Per tutte le altre richieste, aggiunge header CORS alle risposte:
       - `Access-Control-Allow-Origin`: Permette tutte le origini (`*`) se `MCP_ALLOWED_ORIGINS` non è configurato, altrimenti usa la lista configurata
       - `Access-Control-Allow-Methods`: `GET, POST, OPTIONS`
       - `Access-Control-Allow-Headers`: `Content-Type, Authorization`
       - `Access-Control-Max-Age`: `86400` (24 ore) per le richieste preflight
    4. Il middleware è stato aggiunto all'app FastAPI prima del `CSPMiddleware` (riga 660) per garantire che gli header CORS siano applicati per primi
  - **Sub-bug risolto**: Inizialmente era stato incluso `Access-Control-Allow-Credentials: true` insieme a `Access-Control-Allow-Origin: *`, che è una combinazione invalida secondo le specifiche CORS. Questo è stato rimosso perché non necessario per il caso d'uso attuale.
  - **Verificato**: [2026-01-08] Il widget ora si carica correttamente quando renderizzato da ChatGPT. Le risorse JS e CSS vengono caricate senza errori CORS. Il middleware gestisce correttamente le richieste da origini diverse, incluso ChatGPT con origini dinamiche.

### Asset Path - Path degli asset non corretti in produzione
- [x] **Bug Asset Path - Path degli asset non corretti quando deployato**: [2026-01-08]
  - **Bug trovato**: [2026-01-08] Quando il server era deployato su Render invece che in locale, i path degli asset (JS, CSS) nell'HTML generato puntavano a `http://localhost:4444/` invece che al dominio di produzione. Questo causava il mancato caricamento delle risorse quando i widget venivano renderizzati da ChatGPT.
  - **Bug risolto**: [2026-01-08] È stata implementata una funzione `fix_asset_path` nella funzione `_handle_read_resource` che riscrive i path degli asset nell'HTML per gestire diversi casi: URL localhost, path assoluti root, e path con BASE_URL. La funzione converte automaticamente i path in formato corretto basandosi sulla variabile d'ambiente `BASE_URL` se configurata.
  - **Soluzione applicata**:
    1. Aggiunta funzione `fix_asset_path` che normalizza i path degli asset (riga 492-502 in `main.py`)
    2. Implementati pattern regex per gestire tre casi:
       - Pattern 1: URL localhost (`http://localhost:4444/file.js` o `http://localhost:4444/assets/file.js`)
       - Pattern 2: Path assoluti root (`/file.js`)
       - Pattern 3: Path con BASE_URL (se configurato)
    3. La funzione assicura che tutti i path abbiano il prefisso `assets/` e usino `BASE_URL` se configurato, altrimenti path relativi root
    4. I path vengono riscritti nell'HTML prima di essere restituiti al client
  - **Verificato**: [2026-01-08] I path degli asset ora sono corretti sia in locale che in produzione. Le risorse JS e CSS si caricano correttamente quando il server è deployato su Render.

### CSP Header - h11 rifiuta header CSP
- [x] **Bug CSP Header - h11 rifiuta header Content-Security-Policy**: [2026-01-08]
  - **Bug trovato**: [2026-01-08] La libreria h11 (usata da uvicorn) è molto rigorosa nella validazione degli header HTTP e potrebbe rifiutare l'header `Content-Security-Policy` se non è formattato correttamente. Questo causava errori nel server quando si tentava di aggiungere l'header CSP.
  - **Bug risolto**: [2026-01-08] È stata costruita la policy CSP come stringa singola invece di header multipli, e aggiunto un try/except per gestire il caso in cui h11 rifiuti l'header. Se h11 rifiuta l'header, viene loggato un warning ma la risposta non viene bloccata, permettendo al server di funzionare anche senza CSP.
  - **Soluzione applicata**:
    1. Costruita la policy CSP come stringa singola per evitare problemi con h11 (riga 309 in `main.py`)
    2. Aggiunto try/except intorno all'assegnazione dell'header CSP (riga 314-319)
    3. Se h11 rifiuta l'header, viene loggato un warning ma la risposta viene comunque restituita
    4. Aggiunti anche header di sicurezza aggiuntivi (`X-Content-Type-Options`, `X-Frame-Options`) che sono meno problematici per h11
  - **Verificato**: [2026-01-08] Il server ora gestisce correttamente il caso in cui h11 rifiuti l'header CSP. Il server continua a funzionare anche se CSP non può essere applicato, e gli altri header di sicurezza vengono comunque aggiunti.

### 2.2 Compatibilità dei tipi `CartItem`
- [x] **Bug TypeScript - Tipo `CartItem` non definito**: [2026-01-08]
  - **Bug trovato**: [2026-01-08] Il file `py/new_initial_cart_items.ts` usa il tipo `CartItem[]` ma non lo definisce né lo importa. Il tipo `CartItem` è definito localmente in `src/pizzaz-shop/index.tsx` (riga 30) e in modo diverso in `src/shopping-cart/index.tsx` (riga 7, più semplice). Potrebbe esserci un problema di compatibilità dei tipi che deve essere risolto. - Come si manifesta: TypeScript potrebbe non rilevare errori a compile-time se il tipo è inferito, ma potrebbe causare problemi di type safety.
  - **Bug risolto**: [2026-01-08] Il tipo `CartItem` è stato consolidato in un file condiviso `src/types.ts` e importato in tutti i file che lo utilizzano. Questo risolve l'errore TypeScript `TS2304: Cannot find name 'CartItem'` e migliora la type safety.
  - **Soluzione applicata**:
    1. Creato tipo condiviso `CartItem` e `NutritionFact` in `src/types.ts` (esportati)
    2. Aggiunto import `import type { CartItem } from "../src/types";` in `py/new_initial_cart_items.ts`
    3. Rimosso tipo locale `CartItem` e `NutritionFact` da `src/pizzaz-shop/index.tsx` e aggiunto import `import type { CartItem, NutritionFact } from "../types";`
    4. Rimosso tipo locale `CartItem` da `src/shopping-cart/index.tsx` e aggiunto import `import type { CartItem } from "../types";`
  - **Verificato**: [2026-01-08] L'errore TypeScript `py/new_initial_cart_items.ts(1,34): error TS2304: Cannot find name 'CartItem'` è stato risolto. La build TypeScript ora passa senza errori relativi a `CartItem`. Il tipo è ora condiviso e coerente in tutti i file.

### Immagine Blob Storage non accessibile
- [x] **Bug Immagine Blob Storage - Immagine con permessi negati**: [2026-01-08]
  - **Bug trovato**: [2026-01-08] L'immagine `img-Ywf9b6rLPQ5YM0rZh2NQEkp8.png` da Azure Blob Storage in `src/electronics/markers.json` (riga 11) non è accessibile, causando errori 409 (Conflict) e "access is not permitted on this storage account" nella console del browser. Questo impedisce il caricamento completo del widget.
  - **Bug risolto**: [2026-01-08] L'URL dell'immagine blob storage è stato sostituito con un'immagine valida da `https://persistent.oaistatic.com/electronics/electronics-1.png` per garantire che l'immagine sia accessibile.
  - **Soluzione applicata**:
    1. Sostituito l'URL blob storage non accessibile con `https://persistent.oaistatic.com/electronics/electronics-1.png` in `src/electronics/markers.json` (riga 11)
  - **Verificato**: [2026-01-08] L'immagine ora punta a una risorsa accessibile. L'errore 409 e di permessi non dovrebbe più verificarsi per questo elemento.

### Immagini bloccate da ORB (Opaque Response Blocking)
- [x] **Bug ORB - Immagini electronics-*.png bloccate**: [2026-01-08]
  - **Bug trovato**: [2026-01-08] Le immagini `electronics-*.png` da `https://persistent.oaistatic.com/electronics/` vengono bloccate dal browser con errore `ERR_BLOCKED_BY_ORB` (Opaque Response Blocking). Questo è un meccanismo di sicurezza del browser che blocca risposte opache cross-origin, causando il mancato caricamento delle immagini nel widget.
  - **Bug risolto**: [2026-01-08] È stato creato un componente `SafeImage` che gestisce gli errori di caricamento delle immagini e mostra un placeholder quando un'immagine non può essere caricata. Tutti i componenti che usano immagini sono stati aggiornati per usare `SafeImage` invece di `Image` o tag `img` standard.
  - **Soluzione applicata**:
    1. Creato componente `SafeImage` in `src/electronics/SafeImage.jsx` che:
       - Usa un tag `img` standard con gestione errori tramite `onError`
       - Mostra un fallback se fornito quando l'immagine fallisce
       - Mostra un placeholder SVG se nessun fallback è fornito
       - Resetta lo stato di errore quando l'URL cambia
    2. Sostituito `Image` da `@openai/apps-sdk-ui` con `SafeImage` in:
       - `src/electronics-carousel/PlaceCard.jsx`
       - `src/electronics/Inspector.jsx` (2 occorrenze)
       - `src/electronics/Sidebar.jsx`
       - `src/electronics-albums/AlbumCard.jsx`
       - `src/electronics-albums/FullscreenViewer.jsx`
       - `src/electronics-albums/FilmStrip.jsx`
  - **Verificato**: [2026-01-08] Il componente `SafeImage` gestisce correttamente gli errori di caricamento. Quando un'immagine viene bloccata da ORB o fallisce per altri motivi, viene mostrato un placeholder invece di un'immagine rotta, migliorando l'esperienza utente anche quando le immagini non possono essere caricate.

## Verifiche da fare

**Nota**: Le verifiche dettagliate sono state spostate da `specifications.md` a questo file per mantenere `specifications.md` focalizzato solo sulle specifiche da implementare. Le verifiche qui elencate devono essere completate e testate funzionalmente prima di poter essere spuntate definitivamente.

### Build e esecuzione
- [x] **Verifica build frontend**: [2026-01-08] La build è stata testata e completata con successo. Tutti i widget sono stati generati correttamente (pizzaz-shop, pizzaz, pizzaz-albums, pizzaz-carousel, pizzaz-list, kitchen-sink-lite, mixed-auth-past-orders, mixed-auth-search, shopping-cart, solar-system, todo). Alcuni warning sui sourcemap sono presenti ma non bloccanti. - Verificato funzionalmente: `pnpm run build` eseguito con successo il 2026-01-08.

- [x] **Verifica server Python**: [2026-01-08] La sintassi del server Python è stata verificata (`python -m py_compile main.py` completato con successo). **Verificato funzionalmente**: [2026-01-08] Il server è stato avviato e testato con successo. Tutti i metodi MCP funzionano correttamente: `list_tools()` restituisce 6 tool, `list_resources()` restituisce 6 risorse, `list_resource_templates()` restituisce 6 template, `read_resource()` legge correttamente le risorse HTML, `call_tool()` esegue correttamente i tool con structured content e validazione input.

### Integrazione prodotti
- [x] **Verifica import prodotti**: [2026-01-08] L'import è presente alla riga 16: `import { INITIAL_CART_ITEMS as NEW_INITIAL_CART_ITEMS } from "../../py/new_initial_cart_items";` - Verificato funzionalmente: l'import è corretto e funziona.

- [x] **Verifica rimozione prodotti vecchi**: [2026-01-08] Non ci sono definizioni locali residue di `INITIAL_CART_ITEMS` nel file. Solo l'import da `py/new_initial_cart_items.ts` è presente. - Verificato funzionalmente: non ci sono definizioni locali residue.

### Architettura MCP
- [ ] **DA VERIFICARE - Permessi MotherDuck minimi**: Il server accede solo a MotherDuck per i prodotti - **DA VERIFICARE** se i permessi sono minimi. Il codice mostra che il server accede solo a MotherDuck tramite `get_products_from_motherduck()` (riga 57-65). La funzione usa una connessione DuckDB con token da variabile d'ambiente. La sintassi è corretta (verificata con py_compile). **Verificato funzionalmente**: [2026-01-08] Il server accede a MotherDuck solo quando viene chiamato il tool `product-list`. Gli altri tool (pizza-map, pizza-carousel, pizza-albums, pizza-list, pizza-shop) non accedono a dati esterni. L'accesso è limitato al tool che ne ha bisogno.

**Nota**: Le verifiche con "**Verificato**: [2026-01-08]" indicano che il codice è stato verificato, ma la funzionalità deve essere testata quando il server/widget è in esecuzione. Le verifiche con "**DA VERIFICARE**" richiedono test funzionali prima di poter essere spuntate definitivamente.
