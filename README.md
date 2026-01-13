# Sports-Card-Checker

## What this repo will become

A web app where users catalogue sports trading-cards (NHL / MLB / NBA / NFL) and fetch live eBay sold prices. **Important** As of now the live server for the backend no longer works since the free trial is over. To view project please run locally.

---

## Dependencies:

    1. Install Node + npm (for React / Vite)
    2. Install Python ≥ 3.10

## 1. One-time local setup

### 1.1 Clone & root folder

```bash
1. git clone https://github.com/Dante-hu/Sports-Card-Checker.git

2. cd Sports-Card-Checker
```

## 2. Python Backend

```
1. python -m venv venv  #windows
2. venv/Scripts/activate
3. pip install -r requirements.txt
```

## 3. React Frontend

```bash
1. cd client
2. npm install
```
## 4. Docker

To run the backend and Postgres using Docker:

### Build the containers
```bash
docker compose build
```
### Start Everything
```bash
docker compose up
```
### Rebuild after code changes
```bash
docker compose up --build
```
## 5. How to run Locally
1. Navigate to the /server directory and run the following command to run and populate the backend
```bash
python -m flask --app app:create_app run --debug
```
If the database is already populated you can simply run 'flask run'

2. Navigate to the client directory /client and run the following command
```bash
npm run dev
```

