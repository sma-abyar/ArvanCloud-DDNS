import requests
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import time
import configparser
import os
from ttkthemes import ThemedTk

auto_update_flag = False

def get_public_ip():
    try:
        return requests.get("https://api.ipify.org").text
    except requests.RequestException as e:
        messagebox.showerror("Error", f"Failed to get public IP: {e}")
        return None

# Save and Load config file
def save_config():
    config = configparser.ConfigParser()
    config['DEFAULT'] = {
        'ApiKey': api_key_entry.get(),
        'RecordName': record_name_entry.get(),
        'Domain': domain_entry.get(),
        'RecordID': record_id_entry.get(),
        'RecordType': record_type_entry.get(),
        'Interval': interval_entry.get()
    }
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    messagebox.showinfo("Info", "Configuration saved successfully.")

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    if 'DEFAULT' in config:
        api_key_entry.delete(0, tk.END)
        api_key_entry.insert(0, config['DEFAULT'].get('ApiKey', ''))

        record_name_entry.delete(0, tk.END)
        record_name_entry.insert(0, config['DEFAULT'].get('RecordName', ''))

        domain_entry.delete(0, tk.END)
        domain_entry.insert(0, config['DEFAULT'].get('Domain', ''))

        record_id_entry.delete(0, tk.END)
        record_id_entry.insert(0, config['DEFAULT'].get('RecordID', ''))

        record_type_entry.delete(0, tk.END)
        record_type_entry.insert(0, config['DEFAULT'].get('RecordType', ''))

        interval_entry.delete(0, tk.END)
        interval_entry.insert(0, config['DEFAULT'].get('Interval', ''))

def check_dns_record(api_key, domain, record_id):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': api_key
    }
    response = requests.get(f"https://napi.arvancloud.ir/cdn/4.0/domains/{domain}/dns-records/{record_id}", headers=headers)
    if response.status_code == 200:
        records = response.json()
        return records["data"]["value"][0]["ip"]
    return None

def update_dns_record():
    api_key = api_key_entry.get()
    record_name = record_name_entry.get()
    domain = domain_entry.get()
    record_id = record_id_entry.get()
    record_type = record_type_entry.get()
    current_ip = get_public_ip()

    record_id = record_id.strip()
    dns_record_ip = check_dns_record(api_key, domain, record_id)

    if dns_record_ip == current_ip:
        result_text.insert(tk.END, f"Info: The IP address already matches the A record for {record_name} ({dns_record_ip}).\n")
        return

    elif dns_record_ip is None:
        result_text.insert(tk.END, f"Error: Could not retrieve the DNS record for {record_name}.\n")
        return

    headers = {
        'Content-Type': 'application/json',
        'Authorization': api_key
    }

    data = {
        "value": [
            {
                "ip": current_ip,
                "port": 80,
                "weight": 1000,
                "country": "US"
            }
        ],
        "type": record_type,
        "name": record_name,
        "ttl": 120,
        "cloud": False,
        "upstream_https": "default",
        "ip_filter_mode": {
            "count": "single",
            "order": "none",
            "geo_filter": "none"
        }
    }

    try:
        response = requests.put(f"https://napi.arvancloud.ir/cdn/4.0/domains/{domain}/dns-records/{record_id}", json=data, headers=headers)
        if response.status_code == 200:
            result_text.insert(tk.END, f"Success: DNS record for {record_name} updated successfully.\n")
        else:
            result_text.insert(tk.END, f"Error: Failed to update DNS record for {record_name}: {response.text}\n")
    except requests.RequestException as e:
        result_text.insert(tk.END, f"API request failed for {record_name}: {e}\n")

def auto_update():
    global auto_update_flag
    auto_update_flag = True
    record_id = record_id_entry.get()
    interval_str = interval_entry.get()
    interval = float(interval_str) * 60 if interval_str else 0  # Convert minutes
    if interval == 0:
        auto_update_flag = False
    while auto_update_flag:
        for remaining in range(int(interval), 0, -1):
            mins, secs = divmod(remaining, 60)
            countdown_label.config(text=f"Next check in: {mins:02d}:{secs:02d}")
            root.update()
            time.sleep(1)
            if not auto_update_flag:
                break

        countdown_label.config(text="Checking...")
        if auto_update_flag:
            current_ip = get_public_ip()
            ip_label.config(text=current_ip)
            update_performed = False
            record_id = record_id.strip()
            dns_record_ip = check_dns_record(api_key_entry.get(), domain_entry.get(), record_id)
            if current_ip != dns_record_ip:
                update_dns_record()
                update_performed = True
            if not update_performed:
                result_text.insert(tk.END, f"No update necessary at {time.strftime('%Y-%m-%d %H:%M:%S')}.\n")
        countdown_label.config(text="Update check completed.")

def stop_auto_update():
    global auto_update_flag
    auto_update_flag = False

# GUI Setup
root = ThemedTk(theme="arc")
root.title("Arvan DNS Updater")

# Public IP Display
ip_label_frame = ttk.LabelFrame(root, text="Your Public IP:")
ip_label_frame.pack(padx=10, pady=5, fill="x")
ip_label = ttk.Label(ip_label_frame, text=get_public_ip())
ip_label.pack(padx=10, pady=5)

# Save and Load Buttons
button_frame = ttk.Frame(root)
button_frame.pack(padx=10, pady=5, fill="x")

save_config_button = ttk.Button(button_frame, text="Save Config", command=save_config)
save_config_button.grid(row=0, column=0, padx=5, pady=5)

load_config_button = ttk.Button(button_frame, text="Load Config", command=load_config)
load_config_button.grid(row=0, column=1, padx=5, pady=5)

# Input Fields with Labels
inputs_frame = ttk.LabelFrame(root, text="Configuration")
inputs_frame.pack(padx=10, pady=5, fill="both")

api_key_label = ttk.Label(inputs_frame, text="API Key:")
api_key_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
api_key_entry = ttk.Entry(inputs_frame)
api_key_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

record_name_label = ttk.Label(inputs_frame, text="Record Name:")
record_name_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
record_name_entry = ttk.Entry(inputs_frame)
record_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

domain_label = ttk.Label(inputs_frame, text="Domain:")
domain_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
domain_entry = ttk.Entry(inputs_frame)
domain_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

record_id_label = ttk.Label(inputs_frame, text="Record ID:")
record_id_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
record_id_entry = ttk.Entry(inputs_frame)
record_id_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

record_type_label = ttk.Label(inputs_frame, text="Record Type:")
record_type_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
record_type_entry = ttk.Entry(inputs_frame)
record_type_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

# Update Button
update_button = ttk.Button(root, text="Update DNS Record", command=update_dns_record)
update_button.pack(pady=5)

# Interval Input Field
interval_frame = ttk.LabelFrame(root, text="Update Interval (minutes):")
interval_frame.pack(padx=10, pady=5, fill="both")

interval_entry = ttk.Entry(interval_frame)
interval_entry.pack(padx=10, pady=5, fill="x")

# Start and Stop Auto-Update Buttons
auto_update_frame = ttk.Frame(root)
auto_update_frame.pack(padx=10, pady=5, fill="x")

start_auto_update_button = ttk.Button(auto_update_frame, text="Start Auto Update", command=lambda: threading.Thread(target=auto_update, daemon=True).start())
start_auto_update_button.grid(row=0, column=0, padx=5, pady=5)

stop_auto_update_button = ttk.Button(auto_update_frame, text="Stop Auto Update", command=stop_auto_update)
stop_auto_update_button.grid(row=0, column=1, padx=5, pady=5)

# Result Text Widget
result_text_frame = ttk.LabelFrame(root, text="Logs")
result_text_frame.pack(padx=10, pady=5, fill="both", expand=True)

result_text = tk.Text(result_text_frame, height=10)
result_text.pack(padx=10, pady=5, fill="both", expand=True)

result_scroll = ttk.Scrollbar(result_text_frame, orient="vertical", command=result_text.yview)
result_scroll.pack(side="right", fill="y")
result_text.config(yscrollcommand=result_scroll.set)

# Countdown timer
countdown_frame = ttk.Frame(root)
countdown_frame.pack(padx=10, pady=5, fill="x")

countdown_label = ttk.Label(countdown_frame, text="Next check in: --:--")
countdown_label.pack(side="left", padx=(0, 10), pady=5)

def start_auto_update_thread():
    threading.Thread(target=auto_update, daemon=True).start()

# Check for config.ini and load if exists
if os.path.exists('config.ini'):
    load_config()
    start_auto_update_thread()

root.mainloop()
