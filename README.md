# challenge3-broken-login

**CTF Challenge 3: The Broken Login** | Web | Beginner | 150 points
Learning goals: SQL injection, insecure authentication queries, parameterized SQL.

> **WARNING: this app is intentionally vulnerable.** Deploy it only in an isolated educational environment (a throwaway VM or container on a lab network). Never run it on a machine that holds real data, and do not reuse its code in real projects.

This repository contains only the standalone challenge app. It does not include or modify CTFd.

## Player-facing description
> A legacy employee portal protects its internal dashboard with a login form. Unfortunately, the authentication system was built without following secure database query practices.
>
> Can you identify the vulnerability and access the restricted dashboard without knowing a valid password?
>
> Target: Open the challenge application provided by the organizer. Submit the flag you discover to earn points.

## Keep the answer private
The default flag and `SOLUTION.md` live in this repo. **Make the GitHub repository private** (share it with your friend as a collaborator), or delete `SOLUTION.md` and set `CTF_FLAG` as an environment variable on the server. A public repo would let players read the flag.

## Run locally
```bash
git clone <repo-url> challenge3-broken-login
cd challenge3-broken-login
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Environment variables
| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `5000` | Port to listen on |
| `HOST` | `127.0.0.1` | Set `0.0.0.0` so other machines can connect (lab network only) |
| `CTF_FLAG` | `TECH{sqli_login_bypass}` | The flag shown after the bypass |
| `SECRET_KEY` | random per start | Flask session signing key (set a fixed value for stable sessions) |
| `DB_PATH` | `./portal.db` | SQLite file, rebuilt on every start |

Debug mode is always off.

## Verify it works
1. Open the site and sign in with `intern` / `welcome123`. You reach the dashboard with **no flag**.
2. Click **Sign out**, then try `admin' --` with any password. The dashboard shows the flag.
3. Visit `/dashboard` while signed out. You are sent back to the login page.

## Run the tests
```bash
python -m pytest -v
```

## Deploy on a server (friend's setup)
```bash
git clone <repo-url> && cd challenge3-broken-login
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export PORT=8000 SECRET_KEY="$(python3 -c 'import secrets;print(secrets.token_hex(32))')"
export CTF_FLAG='TECH{sqli_login_bypass}'
gunicorn --workers 1 --threads 4 --bind 0.0.0.0:$PORT app:app
```
Keep **one worker** so sessions and the sample database stay consistent.

### Docker
```bash
docker build -t broken-login .
docker run -d --name broken-login -p 8000:5000 -e CTF_FLAG='TECH{sqli_login_bypass}' -e SECRET_KEY=change-me broken-login
```

### About DuckDNS
DuckDNS only gives you a **domain name** that points to an IP address. It does not run the app. The app still needs a real server (a VM, VPS or a machine on your lab network) with the chosen port open. Point a DuckDNS name at that server's public IP, or just share the lab IP directly.

### Isolation advice
- Run it on a dedicated VM or container with nothing else on it.
- Prefer a lab network or VPN. If it must be reachable from the internet, expose only the one port, only during the event, and take it down afterwards.
- The login query opens the database read-only, but treat the whole host as untrusted anyway.

## Add it to CTFd manually
In your existing CTFd admin panel, create a new challenge:
- **Name:** The Broken Login | **Category:** Web | **Value:** 150
- **Description:** the player-facing text above, plus the deployed URL under "Connection Info"
- **Flag** (static, case sensitive): `TECH{sqli_login_bypass}`
- **Hints:** (1) "Think about how what you type in the form ends up inside the database query. What happens if your input contains a quote character?" (2) "In SQL, `--` starts a comment and the rest of the line is ignored. Can you make the query skip the password check for the `admin` account?"
- Set state to Visible when ready. Do not touch Challenge 1 or 2.

## Publish to GitHub
```bash
cd challenge3-broken-login
git init -b main
git add .
git commit -m "Add Challenge 3: The Broken Login"
git remote add origin https://github.com/<your-username>/challenge3-broken-login.git
git push -u origin main
```
Create the empty repo first on github.com (**New repository**, name `challenge3-broken-login`, choose **Private**, do not add a README). Then check the file list on the repo page and share the URL via **Settings > Collaborators**.
