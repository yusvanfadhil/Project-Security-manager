import os
import time
import random
import ipaddress
from datetime import datetime
from getpass import getpass

import mysql.connector
import bcrypt

from rich import box
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "security_asset_db"

RISK_LEVELS          = ["Low", "Medium", "High", "Critical"]
SECURITY_STATUSES    = ["Secure", "Warning", "Compromised"]
MAINTENANCE_STATUSES = ["Scheduled", "In Progress", "Completed"]

STATUS_POINTS = {"Secure": 100, "Warning": 60, "Compromised": 20}

console = Console()

def clear_screen():
    """Clear the terminal window."""
    os.system("cls" if os.name == "nt" else "clear")

def pause():
    input("\nPress Enter to continue... ")

def risk_color(risk):
    """Consistent colors: green=Low, cyan=Medium, yellow=High, red=Critical."""
    return {"Low": "green", "Medium": "cyan",
            "High": "yellow", "Critical": "red"}.get(risk, "white")

def status_display(status):
    """Security status with symbol + color."""
    if status == "Secure":
        return "[green]✓ Secure[/]"
    if status == "Warning":
        return "[yellow]⚠ Warning[/]"
    return "[red]✗ Compromised[/]"

def maint_status_display(status):
    colors = {"Scheduled": "cyan", "In Progress": "yellow", "Completed": "green"}
    return f"[{colors.get(status, 'white')}]{status}[/]"

def score_label(score):
    """Classify the security score."""
    if score >= 80:
        return "🟢 GOOD", "green"
    elif score >= 60:
        return "🔵 MODERATE", "cyan"
    elif score >= 40:
        return "🟡 WARNING", "yellow"
    return "🔴 CRITICAL", "red"

def make_bar(value, max_value, width=20):
    """Return a text bar like ███████░░░░."""
    if max_value <= 0:
        return "░" * width
    filled = round(value / max_value * width)
    return "█" * filled + "░" * (width - filled)

def ask_required(prompt):
    while True:
        value = input(f"{prompt}: ").strip()
        if value:
            return value
        console.print("[yellow]  [!] This field is required![/]")

def ask_default(prompt, current):
    """Ask for a value; pressing Enter keeps the current one."""
    value = input(f"{prompt} [{current}]: ").strip()
    return value if value else current

def ask_choice(prompt, options):
    hint = " / ".join(options)
    while True:
        value = input(f"{prompt} ({hint}): ").strip()
        for opt in options:
            if value.lower() == opt.lower():
                return opt
        console.print("[yellow]  [!] Invalid input! Choose one of the options.[/]")

def ask_choice_or_default(prompt, options, default):
    hint = " / ".join(options)
    while True:
        value = input(f"{prompt} [{default}] ({hint}): ").strip()
        if value == "":
            return default
        for opt in options:
            if value.lower() == opt.lower():
                return opt
        console.print("[yellow]  [!] Invalid input! Choose one of the options.[/]")

def ask_ip(prompt):
    while True:
        value = input(f"{prompt}: ").strip()
        try:
            ipaddress.ip_address(value)
            return value
        except ValueError:
            console.print("[yellow]  [!] Invalid IP address! Example: 192.168.1.10[/]")

def ask_ip_or_default(prompt, default):
    while True:
        value = input(f"{prompt} [{default}]: ").strip()
        if value == "":
            return default
        try:
            ipaddress.ip_address(value)
            return value
        except ValueError:
            console.print("[yellow]  [!] Invalid IP address! Example: 192.168.1.10[/]")

def ask_date(prompt, default=None):
    """Ask for a date (YYYY-MM-DD). Empty = default, or today if no default."""
    hint = default if default else datetime.today().strftime("%Y-%m-%d")
    while True:
        value = input(f"{prompt} [{hint}]: ").strip()
        if value == "":
            return default if default else datetime.today().strftime("%Y-%m-%d")
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            console.print("[yellow]  [!] Invalid date! Use YYYY-MM-DD, e.g. 2026-09-10[/]")

def ask_int(prompt):
    while True:
        value = input(f"{prompt}: ").strip()
        if value.isdigit():
            return int(value)
        console.print("[yellow]  [!] Please enter a number![/]")

def confirm(question):
    return input(f"{question} [y/n]: ").strip().lower() == "y"

def connect_database(use_db=True):
    """Connect to MySQL. use_db=False connects without selecting a database."""
    try:
        if use_db:
            return mysql.connector.connect(
                host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
            )
        return mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD
        )
    except mysql.connector.Error as err:
        console.print(f"[bold red][✗] Cannot connect to MySQL: {err}[/]")
        console.print("[yellow]    Make sure MySQL is running in the XAMPP Control Panel![/]")
        return None

def initialize_database():
    """Create database + 3 tables (runs automatically at startup)."""
    conn = connect_database(use_db=False)
    if conn is None:
        raise SystemExit

    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")  # DB_NAME is a constant, not user input
    cursor.close()
    conn.close()

    conn = connect_database()
    if conn is None:
        raise SystemExit
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id       INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50)  NOT NULL UNIQUE,
            password VARCHAR(100) NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            asset_code      VARCHAR(20)  NOT NULL UNIQUE,
            asset_name      VARCHAR(100) NOT NULL,
            asset_type      VARCHAR(50)  NOT NULL,
            ip_address      VARCHAR(45)  NOT NULL,
            risk_level      VARCHAR(20)  NOT NULL,
            security_status VARCHAR(20)  NOT NULL,
            description     TEXT,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance (
            id               INT AUTO_INCREMENT PRIMARY KEY,
            asset_id         INT         NOT NULL,
            maintenance_date DATE        NOT NULL,
            maintenance_type VARCHAR(50) NOT NULL,
            description      TEXT,
            status           VARCHAR(20) NOT NULL,
            FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    create_default_user()
    insert_dummy_data()
    console.print("[green][✓] Database ready![/]")

def create_default_user():
    """Create admin/admin123 with a bcrypt-hashed password (only once)."""
    conn = connect_database()
    if conn is None:
        return
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = %s", ("admin",))
    if cursor.fetchone() is None:
        hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            ("admin", hashed),
        )
        conn.commit()
        console.print("[green][✓] Default admin account created (admin / admin123).[/]")
    cursor.close()
    conn.close()

def insert_dummy_data():
    """Insert example data ONLY when the tables are empty (never duplicated)."""
    conn = connect_database()
    if conn is None:
        return
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM assets")
    if cursor.fetchone()[0] == 0:
        assets = [
            ("AST-001", "Web Server",      "Server",   "192.168.1.10", "High",     "Secure",      "Main web server"),
            ("AST-002", "Database Server", "Server",   "192.168.1.20", "Critical", "Warning",     "Main database server"),
            ("AST-003", "Main Router",     "Network",  "192.168.1.1",  "Critical", "Secure",      "Core network router"),
            ("AST-004", "Admin PC",        "Endpoint", "192.168.1.25", "Medium",   "Secure",      "Administrator computer"),
            ("AST-005", "Finance PC",      "Endpoint", "192.168.1.30", "High",     "Warning",     "Finance department PC"),
            ("AST-006", "Backup Server",   "Server",   "192.168.1.40", "High",     "Secure",      "Backup storage server"),
            ("AST-007", "Office Laptop",   "Endpoint", "192.168.1.50", "Low",      "Secure",      "General office laptop"),
            ("AST-008", "Firewall",        "Security", "192.168.1.2",  "Critical", "Compromised", "Perimeter firewall"),
        ]
        cursor.executemany(
            """INSERT INTO assets
               (asset_code, asset_name, asset_type, ip_address,
                risk_level, security_status, description)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            assets,
        )
        conn.commit()
        console.print(f"[green][✓] Inserted {len(assets)} dummy assets.[/]")

    cursor.execute("SELECT COUNT(*) FROM maintenance")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT id, asset_name FROM assets")
        name_to_id = {name: asset_id for asset_id, name in cursor.fetchall()}

        maintenance = [
            ("Web Server",      "2026-09-10", "Security Update", "Updated server packages",    "Completed"),
            ("Database Server", "2026-09-11", "Backup Check",    "Verified nightly backups",   "Completed"),
            ("Main Router",     "2026-09-12", "Configuration",   "Reviewed router settings",   "Completed"),
            ("Finance PC",      "2026-09-13", "Antivirus Scan",  "Full system antivirus scan", "In Progress"),
            ("Firewall",        "2026-09-14", "Rule Update",     "Updated firewall rules",     "Completed"),
        ]
        rows = [(name_to_id[name], date, mtype, desc, status)
                for (name, date, mtype, desc, status) in maintenance]
        cursor.executemany(
            """INSERT INTO maintenance
               (asset_id, maintenance_date, maintenance_type, description, status)
               VALUES (%s, %s, %s, %s, %s)""",
            rows,
        )
        conn.commit()
        console.print(f"[green][✓] Inserted {len(rows)} dummy maintenance records.[/]")

    cursor.close()
    conn.close()

def show_login_banner():
    console.print()
    console.print(Panel.fit(
        "[bold cyan]🛡 SECURITY ASSET MANAGER[/]\n\n"
        "[bold white]S Y S T E M   L O G I N[/]",
        border_style="cyan", padding=(1, 10),
    ))
    console.print("[purple]Default login → admin / admin123[/]\n")

def login():
    """Maximum 3 attempts. Returns username or None."""
    attempts_left = 3
    while attempts_left > 0:
        username = input("  Username : ").strip()
        password = getpass("  Password : ")

        conn = connect_database()
        if conn is None:
            return None
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row and bcrypt.checkpw(password.encode("utf-8"), row[0].encode("utf-8")):
            console.print(f"\n[bold green][✓] Login successful! Welcome, {username}[/]")
            return username

        attempts_left -= 1
        if attempts_left > 0:
            console.print(f"[red][✗] Invalid username or password! Attempts left: {attempts_left}[/]\n")
        else:
            console.print("[red][✗] Too many failed attempts! Program closed.[/]")
    return None

def logout():
    console.print("[bold yellow][⎋] You have been logged out.[/]")
    pause()

def calculate_security_score(status_counts, total):
    """Average of: Secure=100, Warning=60, Compromised=20."""
    if total == 0:
        return 100
    points = sum(status_counts.get(s, 0) * pts for s, pts in STATUS_POINTS.items())
    return round(points / total)

def get_statistics():
    """Fetch all numbers from the database using SQL COUNT()."""
    conn = connect_database()
    if conn is None:
        raise SystemExit
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM assets")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT risk_level, COUNT(*) FROM assets GROUP BY risk_level")
    risk_counts = {level: count for level, count in cursor.fetchall()}

    cursor.execute("SELECT security_status, COUNT(*) FROM assets GROUP BY security_status")
    status_counts = {status: count for status, count in cursor.fetchall()}

    cursor.close()
    conn.close()

    return {
        "total":  total,
        "risk":   risk_counts,
        "status": status_counts,
        "score":  calculate_security_score(status_counts, total),
    }

def dashboard(username):
    clear_screen()
    stats = get_statistics()

    console.print(Panel(
        "[bold cyan]🛡 SECURITY ASSET MANAGER[/]   [green]● ONLINE[/]\n"
        f"[bold white]Welcome, {username}[/]",
        border_style="cyan", padding=(0, 2),
    ))

    high_risk = stats["risk"].get("High", 0) + stats["risk"].get("Critical", 0)
    cards = [
        Panel(Text(str(stats["total"]), justify="center", style="bold cyan"),
              title="TOTAL ASSETS", border_style="cyan"),
        Panel(Text(str(high_risk), justify="center", style="bold yellow"),
              title="HIGH RISK", border_style="yellow"),
        Panel(Text(str(stats["status"].get("Secure", 0)), justify="center", style="bold green"),
              title="SECURE", border_style="green"),
    ]
    console.print(Columns(cards, equal=True, expand=True))

    score = stats["score"]
    label, color = score_label(score)
    console.print(Panel(
        f"\n      [{color}]{make_bar(score, 100, 30)}[/]  [bold]{score} / 100[/]\n\n"
        f"                 [bold {color}]{label}[/]\n",
        title="SECURITY SCORE", border_style=color, padding=(0, 2),
    ))

    icons = {"Low": "🟢", "Medium": "🔵", "High": "🟡", "Critical": "🔴"}
    max_count = max(stats["risk"].values(), default=0)
    lines = []
    for level in RISK_LEVELS:
        count = stats["risk"].get(level, 0)
        lines.append(f" {icons[level]}  {level:<9}"
                     f"[{risk_color(level)}]{make_bar(count, max_count, 14)}[/]  {count}")
    console.print(Panel("\n".join(lines) + "\n", title="RISK DISTRIBUTION",
                        border_style="magenta", padding=(0, 2)))

def show_statistics():
    clear_screen()
    stats = get_statistics()
    s, r = stats["status"], stats["risk"]

    console.print(Panel("[bold magenta]        📊 ASSET STATISTICS[/]",
                        border_style="magenta", width=44))
    console.print()
    console.print(f"  Total Assets        : [bold cyan]{stats['total']}[/]")
    console.print(f"  Secure Assets       : [green]{s.get('Secure', 0)}[/]")
    console.print(f"  Warning Assets      : [yellow]{s.get('Warning', 0)}[/]")
    console.print(f"  Compromised Assets  : [red]{s.get('Compromised', 0)}[/]")
    console.print()
    console.print(f"  Low Risk            : [green]{r.get('Low', 0)}[/]")
    console.print(f"  Medium Risk         : [cyan]{r.get('Medium', 0)}[/]")
    console.print(f"  High Risk           : [yellow]{r.get('High', 0)}[/]")
    console.print(f"  Critical Risk       : [red]{r.get('Critical', 0)}[/]")
    console.print()

    score = stats["score"]
    label, color = score_label(score)
    console.print(f"  Security Score      : [bold {color}]{score} / 100[/]  ({label})")
    console.print(f"  [{color}]{make_bar(score, 100, 40)}[/]")

def asset_menu():
    while True:
        clear_screen()
        console.print(Panel(
            "[bold cyan]           🖥 ASSET MANAGEMENT[/]\n\n"
            "  [cyan][1][/] ＋ Add Asset\n"
            "  [cyan][2][/] 📋 View Assets\n"
            "  [cyan][3][/] ✎ Update Asset\n"
            "  [cyan][4][/] × Delete Asset\n"
            "  [red][0][/] ← Back\n",
            border_style="cyan", width=44,
        ))
        choice = input("Select option ❯ ").strip()
        if choice == "1":
            add_asset()
            pause()
        elif choice == "2":
            view_assets()
            pause()
        elif choice == "3":
            update_asset()
            pause()
        elif choice == "4":
            delete_asset()
            pause()
        elif choice == "0":
            return
        else:
            console.print("[yellow][!] Invalid input![/]")
            pause()

def add_asset():
    console.print("\n[bold cyan]────────── ＋ ADD NEW ASSET ──────────[/]")
    asset_code = ask_required("Asset Code (e.g. AST-009)")
    asset_name = ask_required("Asset Name")
    asset_type = ask_required("Asset Type (Server / Network / Endpoint / Security)")
    ip_address = ask_ip("IP Address")
    risk_level = ask_choice("Risk Level", RISK_LEVELS)
    security_status = ask_choice("Security Status", SECURITY_STATUSES)
    description = input("Description (optional): ").strip()

    conn = connect_database()
    if conn is None:
        return
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM assets WHERE asset_code = %s", (asset_code,))
    if cursor.fetchone():
        console.print(f"[red][✗] Asset code '{asset_code}' already exists![/]")
        cursor.close()
        conn.close()
        return

    cursor.execute(
        """INSERT INTO assets
           (asset_code, asset_name, asset_type, ip_address,
            risk_level, security_status, description)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (asset_code, asset_name, asset_type, ip_address,
         risk_level, security_status, description),
    )
    conn.commit()
    cursor.close()
    conn.close()
    console.print(f"[bold green][✓] Asset '{asset_name}' added successfully![/]")

def view_assets():
    conn = connect_database()
    if conn is None:
        return
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, asset_code, asset_name, asset_type, ip_address,
                  risk_level, security_status
           FROM assets ORDER BY id"""
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        console.print("[yellow][!] No assets found. Add one first![/]")
        return

    table = Table(title="🖥 ASSET LIST", border_style="cyan", header_style="bold magenta")
    table.add_column("ID", justify="center")
    table.add_column("CODE", style="cyan")
    table.add_column("ASSET")
    table.add_column("TYPE")
    table.add_column("IP ADDRESS")
    table.add_column("RISK", justify="center")
    table.add_column("STATUS", justify="center")

    for (asset_id, code, name, atype, ip, risk, status) in rows:
        color = risk_color(risk)
        table.add_row(str(asset_id), code, name, atype, ip,
                      f"[bold {color}]{risk.upper()}[/]", status_display(status))
    console.print(table)

def update_asset():
    view_assets()
    asset_id = ask_int("\nAsset ID to update")

    conn = connect_database()
    if conn is None:
        return
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM assets WHERE id = %s", (asset_id,))
    asset = cursor.fetchone()

    if asset is None:
        console.print("[red][✗] Asset not found![/]")
        cursor.close()
        conn.close()
        return

    console.print(f"\n[cyan]Updating:[/] [bold]{asset['asset_name']}[/] "
                  "(press Enter to keep the current value)")

    new_code = ask_default("Asset Code", asset["asset_code"])
    if new_code != asset["asset_code"]:
        cursor.execute(
            "SELECT id FROM assets WHERE asset_code = %s AND id != %s",
            (new_code, asset_id),
        )
        if cursor.fetchone():
            console.print("[red][✗] That asset code is already used by another asset![/]")
            cursor.close()
            conn.close()
            return

    new_name   = ask_default("Asset Name", asset["asset_name"])
    new_type   = ask_default("Asset Type", asset["asset_type"])
    new_ip     = ask_ip_or_default("IP Address", asset["ip_address"])
    new_risk   = ask_choice_or_default("Risk Level", RISK_LEVELS, asset["risk_level"])
    new_status = ask_choice_or_default("Security Status", SECURITY_STATUSES,
                                       asset["security_status"])
    new_desc   = input(f"Description [{asset['description'] or ''}]: ").strip() \
                 or asset["description"]

    cursor.execute(
        """UPDATE assets
           SET asset_code=%s, asset_name=%s, asset_type=%s, ip_address=%s,
               risk_level=%s, security_status=%s, description=%s
           WHERE id=%s""",
        (new_code, new_name, new_type, new_ip, new_risk, new_status, new_desc, asset_id),
    )
    conn.commit()
    cursor.close()
    conn.close()
    console.print("[bold green][✓] Asset updated successfully![/]")

def delete_asset():
    view_assets()
    asset_id = ask_int("\nAsset ID to delete")

    conn = connect_database()
    if conn is None:
        return
    cursor = conn.cursor()
    cursor.execute("SELECT asset_code, asset_name FROM assets WHERE id = %s", (asset_id,))
    asset = cursor.fetchone()

    if asset is None:
        console.print("[red][✗] Asset not found![/]")
        cursor.close()
        conn.close()
        return

    if confirm(f"⚠ Are you sure you want to delete {asset[0]} ({asset[1]})?"):
        cursor.execute("DELETE FROM maintenance WHERE asset_id = %s", (asset_id,))
        cursor.execute("DELETE FROM assets WHERE id = %s", (asset_id,))
        conn.commit()
        console.print("[bold green][✓] Asset deleted successfully![/]")
    else:
        console.print("[yellow]Deletion cancelled.[/]")
    cursor.close()
    conn.close()

def search_asset():
    console.print("\n[bold cyan]🔍 SEARCH ASSET[/]")
    keyword = ask_required("Search (code / name / IP)")

    conn = connect_database()
    if conn is None:
        return
    cursor = conn.cursor()
    like = f"%{keyword}%"

    cursor.execute(
        """SELECT id, asset_code, asset_name, ip_address, risk_level, security_status
           FROM assets
           WHERE asset_code LIKE %s OR asset_name LIKE %s OR ip_address LIKE %s
           ORDER BY id""",
        (like, like, like),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        console.print(f"[yellow][!] No assets found for '{keyword}'[/]")
        return

    console.print(f"\n[green]Found {len(rows)} asset(s):[/]\n")
    table = Table(border_style="cyan", header_style="bold magenta")
    table.add_column("ID", justify="center")
    table.add_column("CODE", style="cyan")
    table.add_column("ASSET")
    table.add_column("IP ADDRESS")
    table.add_column("RISK", justify="center")
    table.add_column("STATUS", justify="center")

    for (asset_id, code, name, ip, risk, status) in rows:
        color = risk_color(risk)
        table.add_row(str(asset_id), code, name, ip,
                      f"[bold {color}]{risk.upper()}[/]", status_display(status))
    console.print(table)

def maintenance_menu():
    while True:
        clear_screen()
        console.print(Panel(
            "[bold yellow]            🔧 MAINTENANCE[/]\n\n"
            "  [cyan][1][/] ＋ Add Maintenance\n"
            "  [cyan][2][/] ◉ View History\n"
            "  [cyan][3][/] ✎ Update Maintenance\n"
            "  [cyan][4][/] × Delete Maintenance\n"
            "  [red][0][/] ← Back\n",
            border_style="yellow", width=44,
        ))
        choice = input("Select option ❯ ").strip()
        if choice == "1":
            add_maintenance()
            pause()
        elif choice == "2":
            view_maintenance()
            pause()
        elif choice == "3":
            update_maintenance()
            pause()
        elif choice == "4":
            delete_maintenance()
            pause()
        elif choice == "0":
            return
        else:
            console.print("[yellow][!] Invalid input![/]")
            pause()

def add_maintenance():
    console.print("\n[bold yellow]────── ＋ ADD MAINTENANCE RECORD ──────[/]")
    view_assets()

    conn = connect_database()
    if conn is None:
        return
    cursor = conn.cursor(dictionary=True)

    asset_id = ask_int("Asset ID")
    cursor.execute("SELECT asset_name FROM assets WHERE id = %s", (asset_id,))
    asset = cursor.fetchone()
    if asset is None:
        console.print("[red][✗] Asset not found![/]")
        cursor.close()
        conn.close()
        return

    date = ask_date("Date")
    mtype = ask_required("Maintenance Type (e.g. Security Update)")
    description = input("Description (optional): ").strip()
    status = ask_choice("Status", MAINTENANCE_STATUSES)

    cursor.execute(
        """INSERT INTO maintenance
           (asset_id, maintenance_date, maintenance_type, description, status)
           VALUES (%s, %s, %s, %s, %s)""",
        (asset_id, date, mtype, description, status),
    )
    conn.commit()
    cursor.close()
    conn.close()
    console.print(f"[bold green][✓] Maintenance added for '{asset['asset_name']}'![/]")

def view_maintenance():
    conn = connect_database()
    if conn is None:
        return
    cursor = conn.cursor()
    cursor.execute(
        """SELECT m.id, a.asset_name, m.maintenance_date, m.maintenance_type,
                  m.description, m.status
           FROM maintenance m
           JOIN assets a ON m.asset_id = a.id
           ORDER BY m.maintenance_date DESC, m.id DESC"""
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        console.print("[yellow][!] No maintenance records found.[/]")
        return

    table = Table(title="🔧 MAINTENANCE HISTORY", border_style="yellow",
                  header_style="bold magenta")
    table.add_column("ID", justify="center")
    table.add_column("ASSET", style="cyan")
    table.add_column("DATE", justify="center")
    table.add_column("TYPE")
    table.add_column("DESCRIPTION")
    table.add_column("STATUS", justify="center")

    for (m_id, name, date, mtype, desc, status) in rows:
        table.add_row(str(m_id), name, str(date), mtype, desc or "-",
                      maint_status_display(status))
    console.print(table)

def update_maintenance():
    view_maintenance()
    m_id = ask_int("\nMaintenance ID to update")

    conn = connect_database()
    if conn is None:
        return
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM maintenance WHERE id = %s", (m_id,))
    record = cursor.fetchone()

    if record is None:
        console.print("[red][✗] Maintenance record not found![/]")
        cursor.close()
        conn.close()
        return

    console.print(f"\n[cyan]Updating record #{m_id}[/] (press Enter to keep the current value)")
    new_date  = ask_date("Date", default=str(record["maintenance_date"]))
    new_type  = ask_default("Maintenance Type", record["maintenance_type"])
    new_desc  = input(f"Description [{record['description'] or ''}]: ").strip() \
                or record["description"]
    new_status = ask_choice_or_default("Status", MAINTENANCE_STATUSES, record["status"])

    cursor.execute(
        """UPDATE maintenance
           SET maintenance_date=%s, maintenance_type=%s, description=%s, status=%s
           WHERE id=%s""",
        (new_date, new_type, new_desc, new_status, m_id),
    )
    conn.commit()
    cursor.close()
    conn.close()
    console.print("[bold green][✓] Maintenance record updated![/]")

def delete_maintenance():
    view_maintenance()
    m_id = ask_int("\nMaintenance ID to delete")

    conn = connect_database()
    if conn is None:
        return
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM maintenance WHERE id = %s", (m_id,))
    if cursor.fetchone() is None:
        console.print("[red][✗] Maintenance record not found![/]")
        cursor.close()
        conn.close()
        return

    if confirm(f"⚠ Are you sure you want to delete maintenance #{m_id}?"):
        cursor.execute("DELETE FROM maintenance WHERE id = %s", (m_id,))
        conn.commit()
        console.print("[bold green][✓] Maintenance record deleted![/]")
    else:
        console.print("[yellow]Deletion cancelled.[/]")
    cursor.close()
    conn.close()

def secret_mode():
    clear_screen()

    console.print(Panel(
        "[bold yellow]          🔐 SECRET MODE ACTIVATED[/]",
        border_style="yellow", box=box.DOUBLE, padding=(1, 4),
    ))
    console.print()

    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ0123456789#$%&"
    for _ in range(5):
        console.print("[green]" + "".join(random.choice(chars) for _ in range(58)) + "[/]")
        time.sleep(0.07)

    with Progress(
        TextColumn("  Initializing security protocols..."),
        BarColumn(bar_width=30, complete_style="green", finished_style="bold green"),
        TextColumn("[bold]{task.percentage:>3.0f}%[/]"),
        console=console,
    ) as progress:
        task = progress.add_task("", total=100)
        while not progress.finished:
            progress.advance(task, random.randint(3, 7))
            time.sleep(0.04)
    console.print()

    db_ok = False
    conn = connect_database()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")                     # tes koneksi
            cursor.execute("SELECT COUNT(*) FROM users")   # tabel users ada?
            cursor.execute("SELECT COUNT(*) FROM assets")  # tabel assets ada?
            cursor.fetchall()
            cursor.close()
            db_ok = True
        except mysql.connector.Error:
            db_ok = False
        conn.close()

    if db_ok:
        checks = [
            ("Database Connection",   "ONLINE"),
            ("Authentication System", "ACTIVE"),
            ("Asset Database",        "PROTECTED"),
            ("Security Monitoring",   "READY"),
        ]
    else:
        checks = [
            ("Database Connection",   "OFFLINE"),
            ("Authentication System", "UNKNOWN"),
            ("Asset Database",        "UNKNOWN"),
            ("Security Monitoring",   "STANDBY"),
        ]

    for name, state in checks:
        with console.status(f"[cyan]Checking {name}...[/]", spinner="dots"):
            time.sleep(0.45)
        ok = state in ("ONLINE", "ACTIVE", "PROTECTED", "READY")
        symbol = "[bold green]✓[/]" if ok else "[bold yellow]![/]"
        color = "green" if ok else "yellow"
        console.print(f"  {symbol} {name:<24} [bold {color}]{state}[/]")

    console.print()
    if db_ok:
        console.print(Panel(
            "[bold green]        SYSTEM STATUS: SECURE 🟢[/]",
            border_style="green", box=box.DOUBLE, padding=(1, 4),
        ))
    else:
        console.print(Panel(
            "[bold yellow]       SYSTEM STATUS: OFFLINE 🟡[/]",
            border_style="yellow", box=box.DOUBLE, padding=(1, 4),
        ))
    pause()

def security_scan():
    """Hidden security scan easter egg using live database data."""
    clear_screen()

    console.print(Panel(
        "[bold green]        🛰 SYSTEM SECURITY SCAN[/]\n"
        "[white]Running live checks against the asset database...[/]",
        border_style="green", box=box.DOUBLE, padding=(1, 4),
    ))
    console.print()

    conn = connect_database()
    if conn is None:
        pause()
        return

    cursor = conn.cursor()

    with console.status("[cyan]Scanning assets...[/]", spinner="dots"):
        cursor.execute("SELECT COUNT(*) FROM assets")
        total = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM assets "
            "WHERE security_status = 'Compromised'"
        )
        compromised = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM assets "
            "WHERE risk_level = 'Critical'"
        )
        critical = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM maintenance "
            "WHERE status = 'In Progress'"
        )
        maintenance_progress = cursor.fetchone()[0]

        time.sleep(0.5)

    cursor.close()
    conn.close()

    checks = [
        ("Asset Records", str(total)),
        ("Critical Risk Assets", str(critical)),
        ("Compromised Assets", str(compromised)),
        ("Maintenance In Progress", str(maintenance_progress)),
    ]

    for name, value in checks:
        console.print(f"  [cyan]▸[/] {name:<26} [bold white]{value}[/]")

    console.print()

    if compromised > 0:
        console.print(
            "[bold red]⚠ THREAT DETECTED:[/] "
            f"{compromised} compromised asset(s) found!"
        )
    elif critical > 0:
        console.print(
            "[bold yellow]⚠ ATTENTION:[/] "
            f"{critical} critical-risk asset(s) found."
        )
    else:
        console.print("[bold green]✓ No immediate threats detected.[/]")

    if maintenance_progress > 0:
        console.print(
            f"[yellow]  • {maintenance_progress} maintenance task(s) "
            "currently in progress.[/]"
        )

    console.print()
    console.print(
        Panel(
            "[bold green]SCAN COMPLETE[/]\n"
            "[white]This easter egg performs a real-time database check.[/]",
            border_style="green",
            padding=(1, 3),
        )
    )
    pause()

def main_menu(username):
    while True:
        clear_screen()
        console.print(Panel(
            f"[bold cyan]🛡 SECURITY ASSET MANAGER[/]  [green]● ONLINE[/]  —  "
            f"[bold white]{username}[/]",
            border_style="cyan", padding=(0, 2),
        ))
        console.print(Panel(
            "[bold magenta]                MAIN MENU[/]\n\n"
            "  [cyan][1][/] 🖥  Asset Management\n"
            "  [cyan][2][/] 🔧 Maintenance\n"
            "  [cyan][3][/] 🔍 Search Asset\n"
            "  [cyan][4][/] 📊 Statistics\n"
            "  [purple][5][/] 🚪 Logout\n"
            "  [red][0][/] ❌ Exit\n",
            border_style="magenta", width=42,
        ))
        choice = input("Select option ❯ ").strip()

        if choice.lower() == "matrix":
            secret_mode()
            continue

        if choice.lower() == "scan":
            security_scan()
            continue

        if choice == "1":
            asset_menu()
        elif choice == "2":
            maintenance_menu()
        elif choice == "3":
            search_asset()
            pause()
        elif choice == "4":
            show_statistics()
            pause()
        elif choice == "5":
            logout()
            return
        elif choice == "0":
            exit_program()
        else:
            console.print("[yellow][!] Invalid input! Please choose 0-5.[/]")
            pause()

def exit_program():
    clear_screen()
    console.print(Panel.fit(
        "[bold cyan]🛡 Thank you for using SECURITY ASSET MANAGER[/]\n"
        "[white]Stay secure! 👋[/]",
        border_style="cyan", padding=(1, 4),
    ))
    raise SystemExit

def main():
    with console.status("[cyan]Preparing database...[/]"):
        initialize_database()
        time.sleep(0.4)   # tiny pause so the loading spinner is visible

    while True:
        clear_screen()
        show_login_banner()
        username = login()
        if username is None:      # 3 failed attempts (or DB offline)
            break
        dashboard(username)       # 2. Modern dashboard
        pause()
        main_menu(username)       # 3. Returns when the user logs out

    console.print("\n[bold cyan]🛡 Goodbye! Stay secure.[/]\n")

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Program closed. Goodbye! 🛡[/]")
    except mysql.connector.Error as err:
        console.print(f"\n[bold red][✗] Database error: {err}[/]")
