"""Tkinter authentication and multi-room chat interface."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from datetime import datetime
from tkinter import ttk
from typing import Any

from .client_core import ChatClient


APP_TITLE = "Python Chat"


class ChatGUI:
    """Render client events and send user actions without blocking Tkinter."""

    def __init__(self, root: tk.Tk, host: str, port: int) -> None:
        self.root = root
        self.client = ChatClient(host, port)
        self.username: str | None = None
        self.current_room_id: int | None = None
        self.room_ids: list[int] = []
        self.authenticated = False
        self.connecting = False

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.auth_error_var = tk.StringVar()
        self.connection_var = tk.StringVar(value=f"Connecting to {host}:{port}…")
        self.logged_in_var = tk.StringVar()
        self.room_heading_var = tk.StringVar(value="Select a room")
        self.room_name_var = tk.StringVar()
        self.message_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Starting chat client…")

        self._configure_window()
        self._configure_styles()
        self._build_interface()
        self._set_auth_enabled(False)
        self._start_connection()
        self.root.after(75, self._poll_events)

    def _configure_window(self) -> None:
        self.root.title(APP_TITLE)
        self.root.geometry("1020x700")
        self.root.minsize(820, 580)
        self.root.configure(bg="#EEF2FF")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<FocusIn>", self._clear_notification)

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("App.TFrame", background="#EEF2FF")
        style.configure("Card.TFrame", background="#FFFFFF")
        style.configure("Sidebar.TFrame", background="#E0E7FF")
        style.configure(
            "Title.TLabel",
            background="#EEF2FF",
            foreground="#111827",
            font=("Segoe UI", 22, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background="#EEF2FF",
            foreground="#4B5563",
            font=("Segoe UI", 10),
        )
        style.configure(
            "CardTitle.TLabel",
            background="#FFFFFF",
            foreground="#111827",
            font=("Segoe UI", 13, "bold"),
        )
        style.configure(
            "CardText.TLabel",
            background="#FFFFFF",
            foreground="#4B5563",
            font=("Segoe UI", 10),
        )
        style.configure(
            "SidebarTitle.TLabel",
            background="#E0E7FF",
            foreground="#312E81",
            font=("Segoe UI", 12, "bold"),
        )
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"))

    def _build_interface(self) -> None:
        container = ttk.Frame(self.root, padding=20, style="App.TFrame")
        container.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        container.rowconfigure(2, weight=1)
        container.columnconfigure(0, weight=1)

        ttk.Label(container, text=APP_TITLE, style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            container,
            text="Real-time rooms, saved history, and emoji shortcodes.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(0, 14))

        self.auth_frame = ttk.Frame(container, padding=24, style="Card.TFrame")
        self.auth_frame.grid(row=2, column=0, sticky="nsew")
        self.auth_frame.columnconfigure(1, weight=1)
        self._build_auth_view()

        self.chat_frame = ttk.Frame(container, style="Card.TFrame")
        self.chat_frame.grid(row=2, column=0, sticky="nsew")
        self.chat_frame.grid_remove()
        self._build_chat_view()

        footer = ttk.Frame(container, style="App.TFrame")
        footer.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status_var, style="Subtitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            footer,
            text="TCP connection — see README for security details",
            style="Subtitle.TLabel",
        ).grid(row=0, column=1, sticky="e")

    def _build_auth_view(self) -> None:
        ttk.Label(self.auth_frame, text="Sign in or register", style="CardTitle.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 6)
        )
        ttk.Label(
            self.auth_frame,
            textvariable=self.connection_var,
            style="CardText.TLabel",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 18))

        ttk.Label(self.auth_frame, text="Username", style="CardText.TLabel").grid(
            row=2, column=0, sticky="w", padx=(0, 12), pady=6
        )
        self.username_entry = ttk.Entry(
            self.auth_frame, textvariable=self.username_var, font=("Segoe UI", 11)
        )
        self.username_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=6)

        ttk.Label(self.auth_frame, text="Password", style="CardText.TLabel").grid(
            row=3, column=0, sticky="w", padx=(0, 12), pady=6
        )
        self.password_entry = ttk.Entry(
            self.auth_frame,
            textvariable=self.password_var,
            show="•",
            font=("Segoe UI", 11),
        )
        self.password_entry.grid(row=3, column=1, columnspan=2, sticky="ew", pady=6)
        self.password_entry.bind("<Return>", lambda _event: self.login())

        self.auth_error_label = tk.Label(
            self.auth_frame,
            textvariable=self.auth_error_var,
            bg="#FEE2E2",
            fg="#991B1B",
            anchor="w",
            padx=10,
            pady=7,
            font=("Segoe UI", 10, "bold"),
        )
        self.auth_error_label.grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=(12, 4)
        )
        self.auth_error_label.grid_remove()

        self.login_button = ttk.Button(
            self.auth_frame,
            text="Log In",
            command=self.login,
            style="Primary.TButton",
        )
        self.login_button.grid(row=5, column=1, sticky="ew", padx=(0, 6), pady=(14, 0))
        self.register_button = ttk.Button(
            self.auth_frame, text="Create Account", command=self.register
        )
        self.register_button.grid(row=5, column=2, sticky="ew", padx=(6, 0), pady=(14, 0))
        self.reconnect_button = ttk.Button(
            self.auth_frame, text="Reconnect", command=self._start_connection
        )
        self.reconnect_button.grid(row=6, column=1, columnspan=2, sticky="ew", pady=(10, 0))

        ttk.Label(
            self.auth_frame,
            text="Username: 3–20 letters/numbers/underscores. Password: at least 8 characters.",
            style="CardText.TLabel",
        ).grid(row=7, column=1, columnspan=2, sticky="w", pady=(14, 0))

    def _build_chat_view(self) -> None:
        self.chat_frame.rowconfigure(0, weight=1)
        self.chat_frame.columnconfigure(1, weight=1)

        sidebar = ttk.Frame(self.chat_frame, padding=14, style="Sidebar.TFrame")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.rowconfigure(2, weight=1)
        sidebar.columnconfigure(0, weight=1)
        ttk.Label(sidebar, text="Chat rooms", style="SidebarTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            sidebar,
            textvariable=self.logged_in_var,
            style="SidebarTitle.TLabel",
            font=("Segoe UI", 9),
        ).grid(row=1, column=0, sticky="w", pady=(2, 10))
        self.room_list = tk.Listbox(
            sidebar,
            width=27,
            exportselection=False,
            font=("Segoe UI", 10),
            bg="#F5F7FF",
            selectbackground="#818CF8",
            selectforeground="#FFFFFF",
            relief="flat",
        )
        self.room_list.grid(row=2, column=0, sticky="nsew")
        self.room_list.bind("<Double-Button-1>", lambda _event: self.join_selected_room())
        ttk.Button(sidebar, text="Join selected", command=self.join_selected_room).grid(
            row=3, column=0, sticky="ew", pady=(8, 12)
        )
        ttk.Entry(sidebar, textvariable=self.room_name_var).grid(
            row=4, column=0, sticky="ew"
        )
        ttk.Button(sidebar, text="Create room", command=self.create_room).grid(
            row=5, column=0, sticky="ew", pady=(6, 0)
        )

        conversation = ttk.Frame(self.chat_frame, padding=16, style="Card.TFrame")
        conversation.grid(row=0, column=1, sticky="nsew")
        conversation.rowconfigure(1, weight=1)
        conversation.columnconfigure(0, weight=1)
        ttk.Label(
            conversation,
            textvariable=self.room_heading_var,
            style="CardTitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        message_area = ttk.Frame(conversation, style="Card.TFrame")
        message_area.grid(row=1, column=0, columnspan=2, sticky="nsew")
        message_area.rowconfigure(0, weight=1)
        message_area.columnconfigure(0, weight=1)
        self.messages = tk.Text(
            message_area,
            wrap="word",
            state="disabled",
            bg="#F9FAFB",
            fg="#1F2937",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 10),
            padx=12,
            pady=10,
        )
        scrollbar = ttk.Scrollbar(message_area, command=self.messages.yview)
        self.messages.configure(yscrollcommand=scrollbar.set)
        self.messages.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.messages.tag_configure("time", foreground="#6B7280")
        self.messages.tag_configure("mine", foreground="#4338CA", font=("Segoe UI", 10, "bold"))
        self.messages.tag_configure("other", foreground="#047857", font=("Segoe UI", 10, "bold"))
        self.messages.tag_configure("system", foreground="#9A3412", font=("Segoe UI", 9, "italic"))

        input_row = ttk.Frame(conversation, style="Card.TFrame")
        input_row.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        input_row.columnconfigure(0, weight=1)
        self.message_entry = ttk.Entry(
            input_row, textvariable=self.message_var, font=("Segoe UI", 11)
        )
        self.message_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.message_entry.bind("<Return>", lambda _event: self.send_message())
        self.send_button = ttk.Button(
            input_row,
            text="Send",
            command=self.send_message,
            style="Primary.TButton",
        )
        self.send_button.grid(row=0, column=1)
        ttk.Label(
            input_row,
            text="Emoji: :smile: :heart: :thumbs_up: :wave: :fire: :party:",
            style="CardText.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(7, 0))

    def _start_connection(self) -> None:
        if self.connecting or self.client.connected:
            return
        self.connecting = True
        self.connection_var.set(f"Connecting to {self.client.host}:{self.client.port}…")
        self._hide_auth_error()
        self.reconnect_button.state(["disabled"])
        threading.Thread(target=self._connect_worker, daemon=True).start()

    def _connect_worker(self) -> None:
        try:
            self.client.connect()
        except ConnectionError as error:
            self.client.events.put({"type": "connection_error", "message": str(error)})

    def login(self) -> None:
        self._submit_auth("login")

    def register(self) -> None:
        self._submit_auth("register")

    def _submit_auth(self, action: str) -> None:
        username = self.username_var.get().strip()
        password = self.password_var.get()
        if not username or not password:
            self._show_auth_error("Enter both username and password.")
            return
        self._send({"type": action, "username": username, "password": password})

    def create_room(self) -> None:
        name = self.room_name_var.get().strip()
        if not name:
            self.status_var.set("Enter a room name first.")
            return
        if self._send({"type": "create_room", "name": name}):
            self.room_name_var.set("")

    def join_selected_room(self) -> None:
        selection = self.room_list.curselection()
        if not selection:
            self.status_var.set("Select a room to join.")
            return
        room_id = self.room_ids[selection[0]]
        self._send({"type": "join_room", "room_id": room_id})

    def send_message(self) -> None:
        text = self.message_var.get().strip()
        if not text:
            return
        if self.current_room_id is None:
            self.status_var.set("Join a room before sending a message.")
            return
        if self._send(
            {"type": "message", "room_id": self.current_room_id, "text": text}
        ):
            self.message_var.set("")

    def _send(self, packet: dict[str, Any]) -> bool:
        try:
            self.client.send(packet)
            return True
        except ConnectionError as error:
            self.status_var.set(str(error))
            if not self.authenticated:
                self._show_auth_error(str(error))
            return False

    def _poll_events(self) -> None:
        try:
            while True:
                packet = self.client.events.get_nowait()
                self._handle_packet(packet)
        except queue.Empty:
            pass
        self.root.after(75, self._poll_events)

    def _handle_packet(self, packet: dict[str, Any]) -> None:
        packet_type = packet.get("type")
        if packet_type == "connected":
            self.connecting = False
            self.connection_var.set(str(packet.get("message", "Connected.")))
            self.status_var.set("Connected. Log in or create an account.")
            self.reconnect_button.state(["disabled"])
            self._set_auth_enabled(True)
        elif packet_type == "connection_error":
            self.connecting = False
            message = str(packet.get("message", "Could not connect."))
            self.connection_var.set(message)
            self._show_auth_error(message)
            self.reconnect_button.state(["!disabled"])
        elif packet_type == "auth_result":
            self._handle_auth_result(packet)
        elif packet_type == "rooms":
            self._update_rooms(packet.get("rooms", []))
        elif packet_type == "join_result":
            self._handle_join(packet)
        elif packet_type == "message":
            self._display_message(packet)
        elif packet_type == "system":
            self._display_system(packet)
        elif packet_type == "error":
            message = str(packet.get("message", "The server rejected the request."))
            if self.authenticated:
                self.status_var.set(message)
                self._append_system(message, packet.get("timestamp"))
            else:
                self._show_auth_error(message)
        elif packet_type in {"disconnected", "server_shutdown"}:
            self._handle_disconnect(str(packet.get("message", "Disconnected.")))

    def _handle_auth_result(self, packet: dict[str, Any]) -> None:
        if not packet.get("ok"):
            self._show_auth_error(str(packet.get("message", "Authentication failed.")))
            return
        self.authenticated = True
        self.username = str(packet.get("username", ""))
        self.password_var.set("")
        self.logged_in_var.set(f"Signed in as {self.username}")
        self.auth_frame.grid_remove()
        self.chat_frame.grid()
        self.status_var.set(str(packet.get("message", "Authenticated.")))

    def _update_rooms(self, rooms: object) -> None:
        if not isinstance(rooms, list):
            return
        self.room_list.delete(0, tk.END)
        self.room_ids.clear()
        for room in rooms:
            if not isinstance(room, dict):
                continue
            room_id = int(room.get("id", 0))
            name = str(room.get("name", "Room"))
            count = int(room.get("message_count", 0))
            self.room_ids.append(room_id)
            self.room_list.insert(tk.END, f"{name}  ({count})")

    def _handle_join(self, packet: dict[str, Any]) -> None:
        room = packet.get("room")
        if not isinstance(room, dict):
            return
        self.current_room_id = int(room.get("id", 0))
        room_name = str(room.get("name", "Room"))
        self.room_heading_var.set(f"# {room_name}")
        self._clear_messages()
        history = packet.get("history", [])
        if isinstance(history, list):
            for message in history:
                if isinstance(message, dict):
                    self._display_message(message, notify=False)
        self.status_var.set(f"Joined {room_name}. Loaded {len(history)} saved message(s).")
        self.message_entry.focus_set()

    def _display_message(self, packet: dict[str, Any], notify: bool = True) -> None:
        room_id = int(packet.get("room_id", 0))
        if self.current_room_id != room_id:
            return
        username = str(packet.get("username", "Unknown"))
        text = str(packet.get("text", ""))
        timestamp = self._format_timestamp(packet.get("timestamp"))
        self.messages.configure(state="normal")
        self.messages.insert(tk.END, f"[{timestamp}] ", "time")
        self.messages.insert(
            tk.END,
            f"{username}: ",
            "mine" if username.casefold() == (self.username or "").casefold() else "other",
        )
        self.messages.insert(tk.END, f"{text}\n")
        self.messages.configure(state="disabled")
        self.messages.see(tk.END)
        if notify and username.casefold() != (self.username or "").casefold():
            self._notify_if_unfocused(username)

    def _display_system(self, packet: dict[str, Any]) -> None:
        room_id = int(packet.get("room_id", 0))
        if self.current_room_id == room_id:
            self._append_system(str(packet.get("text", "")), packet.get("timestamp"))

    def _append_system(self, text: str, timestamp: object = None) -> None:
        time_text = self._format_timestamp(timestamp)
        self.messages.configure(state="normal")
        self.messages.insert(tk.END, f"[{time_text}] {text}\n", "system")
        self.messages.configure(state="disabled")
        self.messages.see(tk.END)

    def _clear_messages(self) -> None:
        self.messages.configure(state="normal")
        self.messages.delete("1.0", tk.END)
        self.messages.configure(state="disabled")

    def _notify_if_unfocused(self, sender: str) -> None:
        if self.root.focus_displayof() is None or self.root.state() == "iconic":
            self.root.bell()
            self.root.title(f"● {APP_TITLE}")
            self.status_var.set(f"New message from {sender}.")

    def _clear_notification(self, _event: tk.Event[tk.Misc] | None = None) -> None:
        self.root.title(APP_TITLE)

    def _handle_disconnect(self, message: str) -> None:
        self.client.close(notify_server=False)
        self.status_var.set(message)
        if self.authenticated:
            self._append_system(message)
            self.send_button.state(["disabled"])
        else:
            self._show_auth_error(message)
            self.reconnect_button.state(["!disabled"])

    def _set_auth_enabled(self, enabled: bool) -> None:
        state = ["!disabled"] if enabled else ["disabled"]
        self.login_button.state(state)
        self.register_button.state(state)
        if enabled:
            self.username_entry.focus_set()

    def _show_auth_error(self, message: str) -> None:
        self.auth_error_var.set(message)
        self.auth_error_label.grid()

    def _hide_auth_error(self) -> None:
        self.auth_error_var.set("")
        self.auth_error_label.grid_remove()

    @staticmethod
    def _format_timestamp(timestamp: object) -> str:
        if isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp).astimezone().strftime("%H:%M")
            except ValueError:
                pass
        return datetime.now().strftime("%H:%M")

    def close(self) -> None:
        self.client.close()
        self.root.destroy()
