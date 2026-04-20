# Chess Pairings

Webapp per la gestione di tornei di scacchi con struttura, naming e pattern architetturali allineati a `kasparov-webapp`.

## Riferimento architetturale

Il progetto segue i pattern principali di `kasparov-webapp`:

- monorepo con `backend/` e `frontend/`
- backend FastAPI con `async SQLAlchemy`
- configurazione centralizzata in `backend/app/core/config.py`
- sessione DB in `backend/app/core/database.py`
- router sottili in `backend/app/api/`
- business logic e operazioni DB in `backend/app/services/`
- un solo `docker-compose.yml` per sviluppo locale
- frontend con `React Query`, `router/`, `pages/`, `api/customClient.ts`
- client API pensato per convergere su generazione OpenAPI

Scelte di progetto:

- UI con `Tailwind CSS` e componenti locali stile `shadcn/ui`
- dominio applicativo focalizzato su tornei, giocatori, pairings e squadre

## Documentazione

- Requisiti sviluppatore: `docs/requisiti-sviluppatore.md`

## Workflow Git

Il repository e' un monorepo che contiene piu' applicazioni, quindi la convenzione consigliata e' la seguente.

### Branch

- `main`: branch principale di integrazione
- branch brevi per feature o fix, aperte sempre a partire da `main`

Esempi:

- `feature/android-fide-search`
- `feature/chess-pairings-bbp-parser`
- `fix/chess-pairings-round-results`

Non e' consigliato mantenere branch permanenti separati per ogni applicazione.

### Tag di release

Ogni applicazione deve usare tag namespaced, cosi' le release restano indipendenti all'interno dello stesso repository.

Esempi:

- `android/v0.1.0`
- `android/v0.2.0`
- `chess-pairings/v0.1.0`
- `chess-pairings/v0.2.0`

Regole pratiche:

- evitare tag generici come `v0.1.0`
- creare il tag sulla commit di release dopo il merge in `main`
- versionare Android e webapp in modo indipendente

## Stack

### Frontend

- Vite
- React 19
- TypeScript
- Tailwind CSS
- componenti stile shadcn/ui
- React Query
- Axios + axios-case-converter

### Backend

- FastAPI
- SQLAlchemy async
- PostgreSQL
- httpx
- BeautifulSoup

### Tooling

- Docker Compose con un solo file
- Poetry-ready backend tramite `pyproject.toml`
- OpenAPI client workflow predisposto nel frontend

## Struttura repo

```text
chess-pairings/
├── .env.example
├── Makefile
├── docs/
├── docker-compose.yml
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── db/
│   ├── storage/
│   └── app/
│       ├── main.py
│       ├── api/
│       │   ├── deps.py
│       │   ├── health.py
│       │   ├── pairings.py
│       │   ├── players.py
│       │   ├── teams.py
│       │   └── tournaments.py
│       ├── core/
│       │   ├── config.py
│       │   ├── database.py
│       │   └── exceptions.py
│       ├── models/
│       ├── schemas/
│       └── services/
│           ├── bbp_pairings.py
│           ├── fide.py
│           ├── files.py
│           ├── pairing.py
│           ├── player.py
│           ├── standings.py
│           ├── team.py
│           └── tournament.py
└── frontend/
    ├── package.json
    ├── openapi-ts.config.ts
    └── src/
        ├── App.tsx
        ├── main.tsx
        ├── index.css
        ├── api/
        │   ├── client.ts
        │   ├── customClient.ts
        │   ├── queryCacheKeys.ts
        │   ├── queryClient.ts
        │   ├── swagger.yaml
        │   ├── types.ts
        │   └── hooks/
        ├── components/
        ├── pages/
        └── router/
```

## Backend

### Pattern applicato

Come in `kasparov-webapp`, il backend usa:

- `api/` come layer HTTP molto sottile
- `services/` per operazioni DB e logica di dominio
- `core/database.py` per engine async e dependency injection della sessione
- `core/config.py` per variabili ambiente

### Moduli principali

- `services/tournament.py`: CRUD tornei, assegnazione giocatori, serializzazione detail/list item, upload bando
- `services/player.py`: ricerca giocatori locali, import dal catalogo FOA, creazione giocatori
- `services/catalog.py`: import mensile e query del catalogo giocatori su Postgres
- `services/pairing.py`: generazione turni, aggiornamento risultati
- `services/team.py`: CRUD squadre
- `services/standings.py`: classifica e tie-break base
- `services/bbp_pairings.py`: wrapper CLI per `bbpPairings`

### bbpPairings

L'integrazione e' incapsulata nel pattern service-first.

Workflow previsto:

1. caricamento stato torneo dal DB
2. serializzazione in file di lavoro TRF
3. invocazione CLI `bbpPairings`
4. parsing dell'output pairings generato da `bbpPairings -p`
5. persistenza round nel DB

`bbpPairings` e' obbligatorio. Se il binario non e' installato o non e' raggiungibile tramite `BBP_PAIRINGS_BIN`, la generazione pairings fallisce con errore esplicito.

Note operative:

- il binario viene installato nell'immagine Docker del backend in `/usr/local/bin/bbpPairings`
- il sistema Swiss di default usato nel progetto e' `dutch`, che e' l'opzione corretta da passare a `bbpPairings`

### Catalogo giocatori

La ricerca giocatori usa il file mensile locale `backend/data/players_list_foa.txt`. Il catalogo viene importato in una tabella Postgres dedicata, `catalog_player`, usata per la ricerca rapida e per l'import nell'applicazione. Il dataset non e' versionato in Git.

Il comando previsto per rigenerare il catalogo da zero e':

```sh
make build-players-db
```

Il comando:

- svuota la tabella `catalog_player`
- la ricrea a partire dal file TXT aggiornato
- non modifica i record gia' presenti nella tabella applicativa `player`

Campi usati dall'app:

- `ID Number`
- `Name`
- `Fed`
- `SRtng`, con fallback a `RRtng` e `BRtng`
- `Tit` o `OTit` solo se valorizzati

## Frontend

### Pattern applicato

Il frontend adotta:

- `api/customClient.ts`
- hook React Query sottili in `api/hooks/`
- router dedicato in `router/Router.tsx`
- predisposizione per client OpenAPI generato (`openapi-ts.config.ts`)

### Libreria UI

Il frontend usa `Tailwind CSS + shadcn/ui`.

## API disponibili

- `GET /health`
- `GET /api/v1/tournaments/`
- `GET /api/v1/tournaments/{tournament_id}`
- `POST /api/v1/admin/tournaments/`
- `PUT /api/v1/admin/tournaments/{tournament_id}`
- `DELETE /api/v1/admin/tournaments/{tournament_id}`
- `POST /api/v1/admin/tournaments/{tournament_id}/players`
- `POST /api/v1/admin/tournaments/{tournament_id}/bulletin`
- `GET /api/v1/players/`
- `GET /api/v1/players/fide/search`
- `POST /api/v1/admin/players/import-from-fide`
- `GET /api/v1/admin/tournaments/{tournament_id}/teams/`
- `POST /api/v1/admin/tournaments/{tournament_id}/teams/`
- `POST /api/v1/admin/tournaments/{tournament_id}/pairings/generate`
- `PATCH /api/v1/admin/tournaments/{tournament_id}/pairings/results/{pairing_id}`

Swagger:

- `http://localhost:8010/docs`

## Avvio locale

### Docker

```sh
cp .env.example .env.dev
make compose
```

Comandi utili:

- `make compose`
- `make build-players-db`
- `make compose ENV=prod`

## Ambienti

Il progetto usa una configurazione comune in `docker-compose.yml`, un override sviluppo in `docker-compose.dev.yml` e un override produzione in `docker-compose.prod.yml`.

### Development

- env file: `.env` oppure `.env.dev`
- esempio: `.env.example`
- frontend con `vite`
- backend con `uvicorn --reload`
- bind mounts attivi per sviluppo locale
- immagini buildate da `Dockerfile.dev`

Esempio:

```sh
cp .env.example .env.dev
make compose
```

### Production

- env file: `.env.prod`
- esempio: `.env.example`
- frontend buildato statico e servito da Nginx
- backend senza `--reload`
- nessun bind mount del codice applicativo
- immagini buildate da `Dockerfile.prod`
- Postgres non esposto pubblicamente

Esempio:

```sh
cp .env.example .env.prod
make compose ENV=prod
```

Variabili da personalizzare in produzione:

- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `ALLOWED_ORIGINS`
- `FILES_BASE_URL`
- `VITE_API_URL`
- `FRONTEND_PORT` se vuoi esporre il frontend su una porta diversa da `8080`

Per un deploy con domini separati, la configurazione attesa e' questa:

- `app.example.com` verso il container frontend
- `api.example.com` verso il container backend

Il reverse proxy TLS resta esterno a Docker Compose, ad esempio con Nginx o Caddy sul server.

### Produzione su un solo dominio

Non serve per forza un sottodominio separato per le API. Puoi usare:

- frontend: `https://chessdesk.kasparov.polito.it`
- API: `https://chessdesk.kasparov.polito.it/api/...`
- files: `https://chessdesk.kasparov.polito.it/files/...`

In questo caso, in `.env.prod` imposta cosi:

```env
POSTGRES_USER=chess
POSTGRES_PASSWORD=<password-forte>
POSTGRES_DB=chess_pairings
POSTGRES_PORT=5432
BACKEND_PORT=8010
FRONTEND_PORT=8080
DATABASE_URL=postgresql+asyncpg://chess:<password-forte>@postgres:5432/chess_pairings
ALLOWED_ORIGINS=["https://chessdesk.kasparov.polito.it"]
BBP_PAIRINGS_BIN=/usr/local/bin/bbpPairings
BBP_PAIRINGS_SYSTEM=dutch
FILES_BASE_URL=https://chessdesk.kasparov.polito.it
PLAYER_LIST_FILE=/app/data/players_list_foa.txt
VITE_API_URL=https://chessdesk.kasparov.polito.it
```

E' inclusa anche una configurazione Nginx host-level pronta in `deploy/nginx/chessdesk.kasparov.polito.it.conf`.

Deploy tipico sul server:

```sh
cp .env.example .env.prod
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.prod up -d --build
```
- `make logs`
- `make ps`
- `make down`

Servizi esposti:

- backend: `http://localhost:8010`
- frontend: `http://localhost:5173`
- postgres: `localhost:5432`

Per inizializzare o aggiornare il catalogo giocatori dopo aver avviato i container:

```sh
make build-players-db
```

### Backend manuale

```sh
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend manuale

```sh
cd frontend
npm install
npm run dev
```

## Verifiche eseguite

- import backend OK con Python 3.12
- build frontend OK con `npm run build`

## Limiti attuali

- la generazione client OpenAPI e' predisposta ma non ancora agganciata a file generati reali
- non sono ancora presenti auth admin, Alembic e test automatici

## Prossimi miglioramenti consigliati

1. aggiungere Alembic come in `kasparov-webapp`
2. generare davvero `frontend/src/api/client/` da OpenAPI
3. introdurre autenticazione admin e ruoli
4. aggiungere test async backend su standings, catalogo locale giocatori e pairings
5. supportare piu' opzioni avanzate di `bbpPairings` e checklist ufficiale
