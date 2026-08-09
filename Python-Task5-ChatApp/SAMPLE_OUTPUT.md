# Chat Application - Sample Output

This file contains a representative localhost demonstration using fictional
accounts and messages.

## Server startup

```text
Server host: 127.0.0.1
Server port: 5050
Database: chat.db
Status: Listening for client connections
```

## Example client session

```text
[14:30] Alice joined Lobby
[14:31] Bob joined Lobby
[14:31] Alice: Hello Bob!
[14:32] Bob: Hello Alice! :smile:
[14:32] Alice: Welcome to the Python chat project :rocket:
[14:35] Bob disconnected
```

Supported shortcodes such as `:smile:` and `:rocket:` are converted to Unicode
emoji by the client interface.

## Example workflow

```text
1. Start server.py.
2. Start client.py for Alice.
3. Start client.py again for Bob.
4. Register or log in from each client.
5. Join Lobby or create another named room.
6. Exchange messages in real time.
7. Rejoin the room to load its saved message history.
```

## Storage notice

```text
Passwords: Salted PBKDF2 hashes
Messages: Plaintext in SQLite
Network transport: Plain TCP without TLS
End-to-end encryption: Not provided
```

The project is intended for localhost learning and should not be exposed to the
public internet without additional security controls.

