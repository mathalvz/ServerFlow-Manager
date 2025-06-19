<!--
================================================================================
  ServerFlow: Your Intelligent Server Management Platform
================================================================================

  DESCRIPTION:
    ServerFlow is a centralized desktop application designed to simplify the 
    orchestration and management of multiple local services (APIs, databases, 
    frontends) for developers and teams. Leveraging advanced AI integration, 
    ServerFlow streamlines the process of starting, monitoring, and controlling 
    server processes, providing an intuitive and efficient workflow.

  WHO CAN USE SERVERFLOW:
    - Individual developers managing multiple local projects or microservices.
    - Software development teams seeking to streamline local server orchestration.
    - QA engineers and testers needing to spin up and monitor test environments.
    - Educators and students working on software projects with multiple components.
    - Anyone who wants a simple, unified interface for managing local servers.

  MAIN FEATURES:
    - Centralized tabbed dashboard for managing servers, editing configurations, 
      and viewing system logs.
    - Comprehensive server lifecycle management: start, stop, edit, duplicate, 
      and delete server processes safely.
    - Automation capabilities, including autostart and persistent configuration 
      storage in JSON format.
    - Advanced monitoring: real-time and file-based logs, visual status 
      indicators, and port conflict detection.
    - Enhanced convenience: custom HTTP ports, direct browser integration for 
      web/API servers, and user-friendly interface.

  TECHNOLOGIES:
    - Python 3.10+ (recommended: 3.10, 3.11, or 3.12)
    - Tkinter & ttk for GUI
    - subprocess, threading, os, sys, shlex, time, json, re, socket, webbrowser

  INSTALLATION & USAGE:
    1. Ensure Python and Tkinter are installed (see instructions in README).
    2. Clone the repository and navigate to the project directory.
    3. Run the application with `python app.py`.

  PROJECT STRUCTURE:
    - app.py: Main application logic and GUI.
    - server_configs.json: Auto-generated server configurations (not in VCS).
    - logs/: Auto-generated directory for individual server logs.
    - DOCUMENTATION.md: Technical documentation.
    - Example server scripts for Go and Node.js.

  LICENSE:
    MIT License. See LICENSE file for details.

  CONTACT & CONTRIBUTION:
    - Open issues for bug reports or suggestions.
    - Submit pull requests to contribute.
    - Collaboration and feedback are welcome.

  © ServerFlow Manager. Developed with dedication and innovation.
================================================================================
-->
# 🖥️ ServerFlow: Your Intelligent Server Management Platform

> **Simplifying Local Service Orchestration**  
> In the dynamic world of software development, managing multiple local services—APIs, databases, frontends—can be complex. **ServerFlow** is the ultimate solution: an intuitive, centralized desktop platform to start, monitor, and control your servers efficiently.

<!-- Who Can Use ServerFlow -->
<h2>👥 Who Can Use ServerFlow?</h2>
<ul>
  <li><strong>Individual developers</strong> managing several local projects or microservices.</li>
  <li><strong>Software development teams</strong> seeking to streamline local server orchestration.</li>
  <li><strong>QA engineers and testers</strong> who need to spin up and monitor test environments.</li>
  <li><strong>Educators and students</strong> working on software projects with multiple components.</li>
  <li><strong>Anyone</strong> wanting a simple, unified interface for managing local servers.</li>
</ul>

<!-- ServerFlow Advantages -->
<h2>✨ ServerFlow Advantages</h2>
<ul>
  <li><strong>Proficiency in Emerging Technologies:</strong> Advanced AI integration to solve real software challenges.</li>
  <li><strong>Optimized Development Cycle:</strong> Agile prototyping and implementation, prioritizing speed without sacrificing quality.</li>
  <li><strong>Focus on UX and Architecture:</strong> Intuitive interface and modular code, delegating repetitive tasks to AI.</li>
  <li><strong>Accelerated Value Delivery:</strong> Rapid transformation of requirements into tangible, impactful solutions.</li>
</ul>
<p>
For organizations seeking innovation, optimized workflows, and high-quality delivery, this project demonstrates how to leverage AI for development success.
</p>

<!-- Key Features -->
<h2>🚀 Key Features</h2>
<ul>
  <li><strong>Centralized Tabbed Dashboard:</strong> Clean interface with tabs for "Add/Edit Server", "Current Servers", and "System Log".</li>
  <li><strong>Comprehensive Server Management:</strong>
    <ul>
      <li>Controlled process start and stop.</li>
      <li>Safe server editing, duplication, and deletion.</li>
    </ul>
  </li>
  <li><strong>Automation and Persistence:</strong>
    <ul>
      <li>Automatic server startup (autostart).</li>
      <li>Persistent settings in <code>server_configs.json</code>.</li>
    </ul>
  </li>
  <li><strong>Advanced Monitoring and Diagnostics:</strong>
    <ul>
      <li>Dedicated logs per server (real-time and <code>.log</code> files).</li>
      <li>Visual status indicators (Running, Stopped, Starting, Error).</li>
      <li>Port checking to avoid conflicts.</li>
    </ul>
  </li>
  <li><strong>Optimized Convenience:</strong>
    <ul>
      <li>Custom ports for HTTP services.</li>
      <li>Open web/API servers directly in the browser.</li>
    </ul>
  </li>
</ul>

<!-- Technologies Used -->
<h2>🛠️ Technologies Used</h2>

- **Python**: Main programming language (recommended versions: 3.10, 3.11, or 3.12)
- **Tkinter**: Native Python GUI library for building the desktop interface
- **ttk**: Themed Tkinter widgets for a modern look
- **subprocess**: For managing server processes
- **threading**: To handle concurrent operations (e.g., log monitoring)
- **os, sys, shlex, time, json, re, socket, webbrowser**: Standard Python libraries for file operations, configuration, networking, and browser integration

#### How to Install Tkinter

Tkinter is included by default in most Python installations. To check if you have it, run:

```bash
python -m tkinter
```

If a small window appears, Tkinter is installed. If not, install it as follows:

- **On Windows:** Tkinter is included with Python.
- **On Linux (Debian/Ubuntu):**
  ```bash
  sudo apt-get install python3-tk
  ```
- **On macOS:** Tkinter is included with Python from python.org. If using Homebrew Python:
  ```bash
  brew install python-tk
  ```

#### How to Import Tkinter in Your Code

```python
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from tkinter import ttk  # Import Themed Tkinter
import subprocess
import threading
import os
import shlex
import time
import json  # Import for saving/loading configurations
import webbrowser  # Import to open URLs in browser
import re  # Import for regex in load_server_for_editing
import socket  # Import to check ports
import sys  # Import for sys.platform to open logs
```

<!-- How to Set Up and Run -->
<h2>⚙️ How to Set Up and Run</h2>
<ol>
  <li>
    <strong>Prerequisites:</strong>
    <ul>
      <li>Python (recommended: 3.10, 3.11, or 3.12)</li>
      <li><code>live-server</code> (optional, for frontends):<br>
        <code>npm install -g live-server</code>
      </li>
      <li><strong>Tkinter:</strong> See instructions above to ensure Tkinter is installed.</li>
    </ul>
  </li>
  <li>
    <strong>Clone the Repository:</strong>
    <pre><code>git clone https://github.com/your-username/ServerFlow-Manager.git
cd ServerFlow-Manager
</code></pre>
  </li>
  <li>
    <strong>Run the Application:</strong>
    <pre><code>python app.py
</code></pre>
    <em>(or <code>python your_main_file_name.py</code> if renamed)</em>
  </li>
</ol>

<!-- Project Structure -->
<h2>📂 Project Structure</h2>

<pre>
ServerFlow-Manager/
├── .gitignore               # Files ignored by Git
├── app.py                   # Main source code
├── DOCUMENTATION.md         # Technical documentation
├── go_dummy_server.py       # Go server example (Python)
├── node_dummy_server.py     # Node.js server example (Python)
├── LICENSE                  # MIT License
└── README.md                # This file
</pre>
<ul>
  <li><strong>app.py:</strong> GUI (Tkinter), Server class, data persistence.</li>
  <li><strong>server_configs.json:</strong> Server configurations (auto-generated, git-ignored).</li>
  <li><strong>logs/:</strong> Individual log files (auto-generated, git-ignored).</li>
</ul>

<!-- Why ServerFlow -->
<h2>💡 Why ServerFlow?</h2>
<p>
ServerFlow is more than a utility: it's proof that combining development skills and AI can optimize time and efficiency for teams and developers. A step towards a smarter, more centralized workflow.
</p>

<!-- Connect and Collaborate -->
<h2>🤝 Connect and Collaborate</h2>
<p>
I'm always looking for new opportunities to apply and expand my skills in challenging projects. If the vision of AI-driven development resonates with your goals, or if you have suggestions to improve ServerFlow, let's connect!
</p>
<ul>
  <li>Open <strong>Issues</strong> for bugs or suggestions.</li>
  <li>Submit <strong>Pull Requests</strong> to contribute code.</li>
</ul>

<!-- License -->
<h2>📄 License</h2>
<p>
This project is licensed under the <a href="https://opensource.org/licenses/MIT">MIT License</a>.
</p>

<hr>

<p align="center">
  © ServerFlow Manager. Developed with dedication and innovation.
</p>
