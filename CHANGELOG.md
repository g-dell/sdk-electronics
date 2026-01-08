# Changelog

Tutte le modifiche notevoli a questo progetto saranno documentate in questo file.

Il formato è basato su [Keep a Changelog](https://keepachangelog.com/it/1.0.0/),
e questo progetto aderisce a [Semantic Versioning](https://semver.org/lang/it/).

## [1.0.0] - 2026-01-08

### Aggiunto
- Server MCP Python per widget prodotti elettronici
- Integrazione con MotherDuck per recupero prodotti dal database
- 6 tool/widget disponibili:
  - `electronics-map`: Mappa interattiva dei negozi
  - `electronics-carousel`: Carosello prodotti
  - `electronics-albums`: Galleria prodotti
  - `electronics-list`: Lista prodotti
  - `electronics-shop`: Negozio completo
  - `product-list`: Lista prodotti da MotherDuck
- Supporto per risorse MCP (resources e resource templates)
- Transport Security con configurazione `MCP_ALLOWED_HOSTS` e `MCP_ALLOWED_ORIGINS`
- FastAPI app esposta per uvicorn con SSE transport
- Descrizioni dettagliate per tutti i tool
- Documentazione completa nel README

### Note
- Versione iniziale del server
- Richiede `MOTHERDUCK_TOKEN` come variabile d'ambiente obbligatoria
- Supporta MCP Protocol versione 2024-11-05 (Current)
