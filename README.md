# Database/API Server Manager

A powerful desktop application for managing, starting, stopping, and monitoring multiple servers and command-line processes with a user-friendly graphical interface.

---

## 🗒️ Overview

**Database/API Server Manager** is a Python (Tkinter) desktop app designed to streamline the management of various backend servers, APIs, databases, and frontend servers. It centralizes control, eliminating the need for multiple terminals and complex commands—ideal for developers working with diverse local environments.

---

## 🌟 Features

### 1. Add/Edit Server Tab

- **Server Name:** Unique, friendly identifier.
- **Command Type:** Dropdown with presets:
  - Python Script (`.py`)
  - Node.js Script (`.js`)
  - Go App (executable or `.go`)
  - Python SimpleHTTPServer
  - Live-Server (Node.js)
  - MongoDB Daemon
  - PostgreSQL Server
  - Redis Server
  - Custom Command
- **Arguments/Path:** File/folder path or command arguments, with "Browse" support.
- **Working Directory (Optional):** Set execution directory.
- **Port (Optional):** For HTTP servers.
- **Autostart on Open:** Start server automatically with the app.
- **Add/Save Button:** Add new or update existing server.

### 2. Current Servers Tab

- **Dynamic Server List:** Each server as a panel.
- **Actions:**
  - **Start / Stop:** Manage server process.
  - **Edit:** Load config for editing.
  - **Delete:** Remove server (with confirmation).
  - **Duplicate:** Clone server config.
  - **View Log:** Open server log file.
  - **Open in Browser:** For HTTP servers.
- **Status Indicator:**  
  - 🟢 Running  
  - 🟠 Starting/Stopping  
  - 🔴 Error/Exited  
  - ⚪ Stopped
- **Real-time Output:** View stdout/stderr live.

### 3. System Log Tab

- **Internal Logs:** Track app events, errors, and operations for troubleshooting.

---

## 🛠️ Getting Started

### 1. Prerequisites

- **Python:** 3.10, 3.11, or 3.12 recommended.
- **Optional:**  
  - `live-server` (for frontend):  
    ```bash
    npm install -g live-server
    ```

### 2. Running the Application

```bash
python app.py
```

### 3. Adding a Server

1. Go to **Add/Edit Server** tab.
2. Enter server details.
3. Click **Add Server**.

### 4. Managing Servers

- Use **Current Servers** tab for:
  - Start/Stop/Edit/Delete/Duplicate/View Log/Open in Browser

### 5. Monitoring Logs

- View per-server logs and system logs in their respective tabs.

---

## 📂 Project Structure

```
server_manager.py         # Main application file
server_configs.json       # Auto-generated server configs
logs/                    # Per-server log files
node_dummy_server.py      # Example Node.js server (Python)
go_dummy_server.py        # Example Go server (Python)
```

---

## ⚠️ Notes & Considerations

- **Python Version:** Use stable releases (3.10–3.12) for best Tkinter support.
- **PATH:** Ensure commands (node, live-server, mongod, pg_ctl, redis-server) are in your OS PATH or provide full paths.
- **Security:** Only add trusted commands—commands are executed directly.
- **OS Support:** Tested on Windows and Linux. Uses OS-specific methods for opening files/URLs.

---

## License

[MIT](LICENSE)

---

With this documentation, you have a complete overview to get started and make the most of the Database/API Server Manager!
