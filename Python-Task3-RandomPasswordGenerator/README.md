# Task 3 - Secure Random Password Generator

A modular Tkinter password generator that uses Python's `secrets` module for
cryptographically secure random choices. Password history exists only during
the current session and is never saved to disk.

## Features

- Password lengths from 8 to 128 characters
- Uppercase, lowercase, number, and symbol controls
- Requires at least two selected character types
- Guarantees at least one character from every selected type
- Optional exclusion of ambiguous characters such as `0`, `O`, `1`, `l`, and `I`
- Weak, Medium, or Strong visual strength feedback
- Secure shuffle and selection using `secrets`, not `random`
- Automatic clipboard copy after generation and a manual copy button
- Displays only the last five generated passwords in the current session
- Clear-result and clear-history controls

## Requirements

- Python 3.10 or newer
- Tkinter, normally included with the Windows Python installer
- Pyperclip for clipboard access

## Installation

Open PowerShell in this task folder and run:

```powershell
python -m pip install -r requirements.txt
```

## Run the application

Execute only the task's `main.py` file:

```powershell
python main.py
```

Do not run files inside `password_app` directly; they are imported by
`main.py`.

## How to use

1. Choose a password length of at least eight characters.
2. Select at least two character types.
3. Optionally exclude ambiguous characters.
4. Select **Generate password**.
5. The result is copied automatically when clipboard access is available.

Press `Enter` or `Ctrl+G` to generate another password.

## Project files

| File | Purpose |
| --- | --- |
| `main.py` | Creates the Tkinter window and starts the application |
| `password_app/ui.py` | Builds the GUI and coordinates generation, strength, clipboard, and history |
| `password_app/generator.py` | Validates options and securely generates and shuffles passwords |
| `password_app/clipboard.py` | Copies passwords with Pyperclip and normalizes clipboard errors |
| `password_app/history.py` | Maintains the last five passwords in memory |
| `password_app/__init__.py` | Marks `password_app` as a Python package |
| `requirements.txt` | Lists the Pyperclip dependency |

## Security notes

- Password generation uses the cryptographically secure `secrets` module.
- Generated passwords are not written to a file or database.
- Session history disappears when the application closes.
- A copied password remains in the operating system clipboard until it is
  replaced or cleared. Avoid copying passwords on an untrusted computer.

## Troubleshooting

If clipboard copy is unavailable, install dependencies with the same Python
interpreter used to run the application:

```powershell
python -m pip install -r requirements.txt
python main.py
```

The password will still be generated when clipboard integration fails.

## Official reference

- [Python `secrets` documentation](https://docs.python.org/3/library/secrets.html)

