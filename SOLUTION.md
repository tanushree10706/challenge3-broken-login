# SOLUTION.md (organizers only, do not give to players)

**Challenge:** The Broken Login | Web | Beginner | 150 pts | Flag: `TECH{sqli_login_bypass}`

## The vulnerability
`app.py` builds the login query by string concatenation:

```sql
SELECT id, username, password, role, full_name FROM users
WHERE username = '<username>' AND password = '<password>'
```

Whatever the player types becomes part of the SQL itself.

## Intended solve
1. Try a normal login (for example `test` / `test`) and see "Invalid username or password."
2. Type a single quote `'` in the username. The portal reports a database problem, which hints that input reaches SQL.
3. Use a comment to cut off the password check. Username: `admin' --`, password: anything.
   The query becomes `... WHERE username = 'admin' --' AND password = '...'`, so only the username is checked.
4. The dashboard opens and shows the flag.

Other payloads that also work: username `' OR '1'='1' --` (password anything), or password `' OR '1'='1` with any username.

The flag appears only when the returned row does not match the typed credentials exactly. Signing in as `intern` / `welcome123` (a genuine login) opens the dashboard but never shows the flag. The `admin` password is random on every start.

## Suggested CTFd hints
1. (cost 0) "Think about how what you type in the form ends up inside the database query. What happens if your input contains a quote character?"
2. (cost 25) "In SQL, `--` starts a comment and the rest of the line is ignored. Can you make the query skip the password check for the `admin` account?"

## The fix
```python
conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
```
Placeholders keep input as data. Real systems should also store salted password hashes (bcrypt/argon2), never plain text.

## Safety design
- Only the challenge's own SQLite file is reachable, and the login query opens it **read-only**, so `DROP`/`UPDATE`/`INSERT` cannot succeed.
- SQLite runs one statement per call, so stacked queries fail.
- The database is rebuilt on every start. No real credentials or host secrets are involved.
