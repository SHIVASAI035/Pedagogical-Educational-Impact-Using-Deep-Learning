# Pedagogical and Educational Impact Using Deep Learning

A full-stack educational analytics platform that connects student performance,
teaching practice and pedagogical impact. Built with **React + Vite + Tailwind**,
**Flask + JWT + SQLAlchemy**, **MySQL 8**, and a real **TensorFlow/Keras ANN**.

> **Data notice:** the training dataset and the demonstration cohort are
> **synthetic**. They are generated from documented processes and must not be
> presented as real student data. See [`docs/DATASET.md`](docs/DATASET.md).

---

## What it does

| Role | Capabilities |
|---|---|
| **Admin** | Manage accounts, classes and subjects; institution analytics; methodology comparisons; model metrics; dataset management; reports |
| **Teacher** | Assigned students; marks, attendance, assignments and activity; teaching sessions and classroom observations; predictions; feedback insights; multi-indicator teaching analytics; recommendations |
| **Student** | Own marks, attendance, assignments and progress; predicted score; teaching feedback; personalised recommendations |

### Three analytical modules

1. **Student performance** — a 7-feature ANN (`7 → 64 → 32 → 16 → 1`) predicts an
   academic score and flags support needs.
2. **Teacher effectiveness** — feedback and observation indicators, methodology
   mix, data sufficiency and caveats. **No single effectiveness score.**
3. **Pedagogical impact** — Pearson correlations, ANOVA, methodology comparison,
   engagement analysis and KMeans learning patterns, with an explicit
   correlation-is-not-causation statement.

Plus an explainable NLP feedback module (lexicon + rating fusion) and a
rule-based recommendation engine where every suggestion carries its rationale.

---

## Tech stack

- **Frontend:** React 18, Vite 6, Tailwind CSS 3, React Router 6, Axios, Chart.js
- **Backend:** Flask 3, Flask-JWT-Extended, Flask-SQLAlchemy, PyMySQL
- **ML:** TensorFlow 2.21 / Keras 3, Pandas, NumPy, scikit-learn, joblib
- **Database:** MySQL 8.0 (`pedagogical_education_db`)
- **Testing:** pytest (20 tests + optional live MySQL test)

---

## Project structure

```
EDUCATION2/
├── backend/
│   ├── app/
│   │   ├── dataset/            # synthetic dataset generator + CSV
│   │   ├── deep_learning/      # ANN training, predictor, artifacts
│   │   ├── models/             # SQLAlchemy models (15 tables)
│   │   ├── nlp/                # feedback sentiment + aspects
│   │   ├── routes/             # REST blueprints
│   │   ├── services/           # features, analytics, recommendations, accounts
│   │   ├── utils/              # errors, decorators, validation
│   │   ├── __init__.py         # app factory
│   │   └── seed_data.py        # synthetic demo cohort
│   ├── tests/                  # pytest suite
│   ├── config.py
│   ├── run.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/                # axios client
│       ├── auth/               # context + protected routes
│       ├── components/         # layout, charts, UI primitives
│       └── pages/              # admin, teacher, student, shared
├── database/
│   └── schema.sql              # authoritative MySQL DDL
├── docs/
│   ├── API.md
│   ├── DATASET.md
│   └── PROJECT_REPORT.md
└── README.md
```

---

## Quick start (Windows)

### 1. Prerequisites

- Python 3.11+ (tested on 3.13.2)
- Node.js 20+ (tested on 22.13.1)
- MySQL 8.0 running locally

### 2. Create the database

```powershell
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS pedagogical_education_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p pedagogical_education_db < database\schema.sql
```

### 3. Backend

```powershell
cd F:\EDUCATION2\backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

copy .env.example .env
notepad .env
```

Set at least:

```ini
DB_USER=root
DB_PASSWORD=your-mysql-password
DB_NAME=pedagogical_education_db
SECRET_KEY=change-me
JWT_SECRET_KEY=change-me-too
```

Create tables, seed the synthetic cohort, train the ANN and store predictions:

```powershell
.venv\Scripts\python.exe -m app.seed_data --reset
```

Start the API:

```powershell
.venv\Scripts\python.exe run.py
```

- API: http://127.0.0.1:5000
- Health: http://127.0.0.1:5000/api/health

### 4. Frontend

Open a second terminal:

```powershell
cd F:\EDUCATION2\frontend
npm install
npm run dev
```

Open **http://localhost:5173**. Vite proxies `/api` to `http://127.0.0.1:5000`.

### 5. Demo logins

| Role | Email | Password |
|---|---|---|
| Admin | `admin@school.edu` | `Admin@12345` |
| Teacher | `teacher1@school.edu` | `Teacher@12345` |
| Student | `student1001@school.edu` | `Student@12345` |

The login page also has click-to-fill demo buttons.

---

## Useful commands

| Task | Command (from `backend/`) |
|---|---|
| Seed demo data | `.venv\Scripts\python.exe -m app.seed_data --reset` |
| Seed without training | `.venv\Scripts\python.exe -m app.seed_data --reset --skip-train` |
| Train the ANN | `.venv\Scripts\python.exe -m app.deep_learning.train_student_ann` |
| Generate dataset | `.venv\Scripts\python.exe -m app.dataset.generate_dataset --rows 4000 --seed 42` |
| Run tests | `.venv\Scripts\python.exe -m pytest tests -q` |
| Live MySQL test | `$env:TEST_MYSQL="1"; .venv\Scripts\python.exe -m pytest tests\test_mysql_integration.py -q` |
| Frontend dev | `npm run dev` (from `frontend/`) |
| Frontend build | `npm run build` (from `frontend/`) |

The admin UI can also retrain the model and regenerate the dataset from
**Model performance**.

---

## Model evaluation

Real values from the trained model, computed on a 600-row held-out test split:

| Metric | Value |
|---|---|
| MAE | 3.3309 |
| MSE | 17.8828 |
| RMSE | 4.2288 |
| R² | 0.6625 |
| Epochs run | 84 (early stopping) |

These are regenerated by the training run and stored in
`backend/app/deep_learning/artifacts/metrics.json`. Nothing is hard-coded.
Because the data are synthetic, the metrics describe recovery of the documented
data-generating process, **not** real-world predictive power.

---

## Security

- PBKDF2 password hashing (Werkzeug)
- JWT access tokens with role claims
- Role-based decorators and row-level access checks
- Students can only read their own records
- Teachers can only read students and feedback they are entitled to
- Feedback summaries never expose student identity
- Secrets and database credentials live in `backend/.env` (git-ignored)
- CORS restricted to configured frontend origins
- Input validation and consistent JSON error responses

---

## Documentation

- [`docs/PROJECT_REPORT.md`](docs/PROJECT_REPORT.md) — abstract, architecture,
  DFD, ER diagram, ANN design, training, evaluation, modules, results,
  limitations, future work, installation
- [`docs/DATASET.md`](docs/DATASET.md) — synthetic data-generating process,
  schema, preprocessing, limitations
- [`docs/API.md`](docs/API.md) — every endpoint, role, payload and error format
- [`database/schema.sql`](database/schema.sql) — MySQL DDL for all 15 tables

---

## Limitations (read before presenting)

1. The model and demo cohort are **synthetic**.
2. Methodology comparisons are **associations**, not causal effects.
3. The NLP analyser is lexicon-based and misses sarcasm and code-mixing.
4. Teacher indicators are contextual, not a performance rating.
5. The development server is not production-hardened.
6. No fairness audit is possible without demographic attributes.

See `docs/PROJECT_REPORT.md` §15 for the full discussion.
