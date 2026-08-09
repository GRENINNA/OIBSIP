# Task 5 — Chat Application

A modular, real-time chat application built with Python TCP sockets, threads,
Tkinter, and SQLite. No third-party packages are required.

## Run on one computer

Open a terminal in this folder and start the server:

```powershell
python server.py
```

Open two more terminals and start two clients:

```powershell
python client.py
```

Create a different account in each client. Both clients automatically join the
**Lobby**. Messages appear immediately with local timestamp prefixes.

The default address is `127.0.0.1:5050`. A different port can be selected with:

```powershell
python server.py --port 6060
python client.py --port 6060
```

## Features

- User registration and login
- Multiple named rooms with automatic Lobby entry
- Persistent room messages loaded when a room is joined
- Real-time join, leave, and disconnect notices
- In-app notification bell and title badge while the client is unfocused
- Emoji shortcodes including `:smile:`, `:heart:`, `:thumbs_up:`, `:wave:`,
  `:fire:`, `:party:`, `:rocket:`, and `:coffee:`
- Length-prefixed JSON protocol, which safely separates packets over TCP

## Modules

- `server.py` — server launcher
- `client.py` — graphical client launcher
- `chat_app/protocol.py` — length-prefixed JSON packets
- `chat_app/security.py` — password hashing and verification
- `chat_app/database.py` — users, rooms, and history in SQLite
- `chat_app/server_core.py` — connections, rooms, and broadcasts
- `chat_app/client_core.py` — background client transport
- `chat_app/client_ui.py` — Tkinter interface and notifications
- `chat_app/emoji.py` — shortcode conversion

## Security and storage transparency

The server creates `chat.db` in this folder.

- Passwords are **not** stored directly. Each password receives a random salt
  and is processed with PBKDF2-HMAC-SHA256 using 600,000 iterations. The salt,
  derived hash, and iteration count are stored in SQLite.
- Room names, usernames, message text, and timestamps are stored in SQLite.
  **Messages are stored as readable plaintext and are not encrypted at rest.**
- The TCP connection does **not** use TLS. Login passwords and chat messages are
  not encrypted while travelling between client and server.
- This is **not end-to-end encrypted**. The server processes and stores every
  message, and anyone with access to the server or database can read messages.
- Keep the default localhost binding for learning and local demonstrations. Do
  not expose this server to the public internet without adding TLS, stronger
  session controls, abuse prevention, auditing, and a full security review.

To reset all accounts, rooms, and history, stop the server and delete only the
`chat.db` file in this Task 5 folder. A new empty database and Lobby will be
created the next time the server starts.

## Official references

- [Python Socket Programming HOWTO](https://docs.python.org/3/howto/sockets.html)
- [Python `socket` module](https://docs.python.org/3/library/socket.html)
- [Python `sqlite3` module](https://docs.python.org/3/library/sqlite3.html)
- [Python `hashlib.pbkdf2_hmac`](https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac)
