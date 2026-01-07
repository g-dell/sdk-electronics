# Specifiche per l'integrazione dei prodotti e la distribuzione su ChatGPT

Questo documento descrive i passaggi necessari per sostituire i prodotti attuali nell'applicazione Pizzaz con i tuoi prodotti elettronici e per comprendere il deployment su ChatGPT.

## 1. Preparazione dell'ambiente

- [x]  **Comprendere la struttura del progetto**: Familiarizza con i file principali, in particolare `py/new_initial_cart_items.ts` (i tuoi prodotti), `src/pizzaz-shop/index.tsx` (il widget del negozio che usa i prodotti), `src/shopping-cart/index.tsx` (il widget del carrello), `pizzaz_server_python/main.py` (il backend Python) e `package.json` (script di build).

## 2. Integrazione dei prodotti elettronici

### 2.1 Sostituzione di `INITIAL_CART_ITEMS`
- [x]  **Importare i nuovi prodotti**: Modifica `src/pizzaz-shop/index.tsx` per importare `INITIAL_CART_ITEMS` da `py/new_initial_cart_items.ts` invece di usare la definizione locale.
- [x]  **Rimuovere i prodotti vecchi**: Elimina la definizione locale di `INITIAL_CART_ITEMS` in `src/pizzaz-shop/index.tsx`.

### 2.2 Compatibilità dei tipi `CartItem`
- [x]  **Verificare la compatibilità**: Assicurati che il tipo `CartItem` definito in `py/new_initial_cart_items.ts` sia compatibile con quello usato in `src/pizzaz-shop/index.tsx` e `src/shopping-cart/index.tsx`. Potrebbe essere necessario consolidare le definizioni o adattarle.

## 3. Build e esecuzione dell'applicazione

- [x]  **Eseguire la build del frontend**: (Completata con successo) Utilizza i comandi di `pnpm` o `npm` per compilare il frontend, come specificato in `package.json` (es. `pnpm run build`). Questo genererà i file HTML e JavaScript necessari per i widget.
- [x]  **Avviare il server Python**: Esegui il backend Python che serve i widget.

## 4. Distribuzione e interazione con ChatGPT

- [x]  **Chiarire "caricare quest'app su ChatGPT"**: Si intende la realizzazione di un'app per ChatGPT SDK, ospitata su un server e integrata con ChatGPT per mostrare i prodotti elettronici, probabilmente tramite un'azione personalizzata (Custom GPT Action).

### 4.1 Deployment dell'applicazione su Render (Servizio Unico)

- [ ]  **Configurazione del servizio su Render**: Crea un nuovo "Web Service" su Render.
    - [ ]  **Root Directory**: Imposta la "Root Directory" alla radice del tuo repository (`.`).
    - [ ]  **Build Command**: `pnpm install --prefix . && pnpm run build && pip install -r pizzaz_server_python/requirements.txt` (Errore "ModuleNotFoundError: No module named 'duckdb'" risolto aggiungendo `duckdb` a `requirements.txt`.)
    - [ ]  **Start Command**: `uvicorn pizzaz_server_python.main:app --host 0.0.0.0 --port $PORT`
    - [ ]  **Variabili d'ambiente**: Aggiungi `MOTHERDUCK_TOKEN` (con il tuo token), `MCP_ALLOWED_HOSTS`, `MCP_ALLOWED_ORIGINS` (con i domini appropriati, incluso quello di Render) e altre variabili necessarie.

### 4.2 Configurazione di ChatGPT

- [ ]  **Creare una Custom GPT**: Seguire le istruzioni nell'interfaccia di ChatGPT per creare una nuova Custom GPT.
- [ ]  **Configurare un'azione personalizzata**: Aggiungere un'azione al Custom GPT che punta al server Python deployato su Render. Sarà necessario un file OpenAPI che descriva gli endpoint esposti dal server Python. Assicurati che l'URL del server sia l'URL pubblico del tuo servizio Render.

### 4.3 Adattamento degli strumenti (Tools)

- [ ]  **Esaminare la definizione degli strumenti nel backend Python**: Capire come gli strumenti attuali (ad es. "pizza-shop") sono definiti in `pizzaz_server_python/main.py`.
- [ ]  **Modificare o creare nuovi strumenti per i prodotti elettronici**: Adattare gli strumenti esistenti o crearne di nuovi per interagire con i dati dei prodotti elettronici. Ad esempio, potresti voler aggiungere un tool per cercare prodotti specifici o per mostrare i dettagli di un prodotto.

### 4.4 Test e sottomissione

- [ ]  **Testare l'interazione con ChatGPT**: Verificare che ChatGPT possa correttamente invocare gli strumenti e visualizzare i widget con i nuovi prodotti.
- [ ]  **Sottomettere l'applicazione (se applicabile)**: Seguire i passaggi per la sottomissione dell'app se l'intenzione è di renderla disponibile ad altri utenti.