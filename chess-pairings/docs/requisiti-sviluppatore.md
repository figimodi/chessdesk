# Requisiti Per Lo Sviluppatore

Questo documento raccoglie i prerequisiti minimi consigliati per lavorare sul progetto `chess-pairings` in locale.

## Tool richiesti

### Docker

- Docker Engine installato
- Docker Compose installato

Versione consigliata:

- Docker Compose `2.38.2` o compatibile

Nota:

- nel progetto il `Makefile` usa il comando `docker-compose`

### Python

- Python `3.12`

Versione consigliata:

- Python `3.12.12`

Uso nel progetto:

- backend FastAPI
- eventuale esecuzione manuale locale fuori da Docker

### Node.js

- Node.js installato
- npm installato

Versioni consigliate:

- Node.js `24.x`
- npm `11.x`

Uso nel progetto:

- frontend Vite + React
- build frontend
- aggiornamento file OpenAPI frontend

### Make

- `make` installato

Uso nel progetto:

- avvio stack Docker
- consultazione log
- stop/restart/rebuild servizi

## Tool aggiuntivi

### Git

- Git installato

Uso:

- versionamento del codice

### bbpPairings

- binario `bbpPairings` installato e raggiungibile

Uso nel progetto:

- nel progetto `bbpPairings` e' obbligatorio per la generazione dei pairings
- la variabile `BBP_PAIRINGS_BIN` deve puntare al binario corretto
- nel setup Docker del progetto il binario viene installato automaticamente dentro il container backend
- il sistema Swiss di default usato dal progetto e' `dutch`

## File richiesti in locale

Per lavorare correttamente servono anche questi file in locale:

- `.env`
- `backend/data/players_list_foa.txt`

Il file del catalogo giocatori e' richiesto in locale ma non viene versionato in Git.

Il file del catalogo giocatori viene importato nel database tramite il comando:

```sh
make build-players-db
```

Il comando ricrea da zero la tabella `catalog_player` a ogni esecuzione.

Per creare `.env`:

```sh
cp .env.example .env
```

## Verifica rapida ambiente

Comandi utili per controllare le versioni installate:

```sh
python3.12 --version
node --version
npm --version
docker --version
docker-compose version
make --version
```

## Avvio consigliato

Il workflow consigliato per lo sviluppo e' via Docker:

```sh
cp .env.example .env
make compose
```

Servizi esposti:

- frontend: `http://localhost:5173`
- backend: `http://localhost:8010`
- swagger: `http://localhost:8010/docs`
- postgres: `localhost:5432`
