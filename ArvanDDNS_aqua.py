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
        insert_text(f"Info: The IP address already matches the A record for {record_name} ({dns_record_ip}).\n")
        return

    elif dns_record_ip is None:
        insert_text(f"Error: Could not retrieve the DNS record for {record_name}.\n")
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
            insert_text(f"Success: DNS record for {record_name} updated successfully.\n")
        else:
            insert_text(f"Error: Failed to update DNS record for {record_name}: {response.text}\n")
    except requests.RequestException as e:
        insert_text(f"API request failed for {record_name}: {e}\n")

def auto_update():
    global auto_update_flag
    auto_update_flag = True
    record_id = record_id_entry.get()
    interval_str = interval_entry.get()
    interval = float(interval_str) * 60 if interval_str else 0  # Convert minutes to seconds
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
                insert_text(f"No update necessary at {time.strftime('%Y-%m-%d %H:%M:%S')}.\n")
        countdown_label.config(text="Update check completed.")

def stop_auto_update():
    global auto_update_flag
    auto_update_flag = False

# GUI Setup
root = ThemedTk(theme="aquativo")
root.title("Arvan DNS Updater")
root.geometry("600x600")

# Configure grid
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

main_frame = ttk.Frame(root, padding=(10, 10))
main_frame.grid(row=0, column=0, sticky="nsew")

main_frame.columnconfigure(0, weight=1)
main_frame.rowconfigure(1, weight=1)

status_frame = ttk.LabelFrame(main_frame, text="Status", padding=(10, 10))
status_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

status_frame.columnconfigure(1, weight=1)

ttk.Label(status_frame, text="Your Public IP:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
ip_label = ttk.Label(status_frame, text=get_public_ip())
ip_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

countdown_label = ttk.Label(status_frame, text="Next check in: --:--")
countdown_label.grid(row=1, column=0, columnspan=2, pady=5, sticky="w")

inputs_frame = ttk.LabelFrame(main_frame, text="Configurations", padding=(10, 10))
inputs_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

inputs_frame.columnconfigure(1, weight=1)

ttk.Label(inputs_frame, text="API Key:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
api_key_entry = ttk.Entry(inputs_frame)
api_key_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

ttk.Label(inputs_frame, text="Record Name:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
record_name_entry = ttk.Entry(inputs_frame)
record_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

ttk.Label(inputs_frame, text="Domain:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
domain_entry = ttk.Entry(inputs_frame)
domain_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

ttk.Label(inputs_frame, text="Record ID:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
record_id_entry = ttk.Entry(inputs_frame)
record_id_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

ttk.Label(inputs_frame, text="Record Type:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
record_type_entry = ttk.Entry(inputs_frame)
record_type_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

ttk.Label(inputs_frame, text="Update Interval (minutes):").grid(row=5, column=0, padx=5, pady=5, sticky="w")
interval_entry = ttk.Entry(inputs_frame)
interval_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

control_buttons_frame = ttk.Frame(main_frame, padding=(10, 10))
control_buttons_frame.grid(row=2, column=0, pady=10, sticky="ew")

control_buttons_frame.columnconfigure(0, weight=1)

start_auto_update_button = ttk.Button(control_buttons_frame, text="Start Auto Update", command=lambda: threading.Thread(target=auto_update, daemon=True).start())
start_auto_update_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

stop_auto_update_button = ttk.Button(control_buttons_frame, text="Stop Auto Update", command=stop_auto_update)
stop_auto_update_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

save_load_frame = ttk.Frame(main_frame, padding=(10, 10))
save_load_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

save_config_button = ttk.Button(save_load_frame, text="Save Config", command=save_config)
save_config_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

load_config_button = ttk.Button(save_load_frame, text="Load Config", command=load_config)
load_config_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

result_text_frame = ttk.LabelFrame(main_frame, text="Logs", padding=(10, 10))
result_text_frame.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")

result_text_frame.columnconfigure(0, weight=1)
result_text_frame.rowconfigure(0, weight=1)

result_text = tk.Text(result_text_frame, height=10, width=60, wrap=tk.WORD)
result_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

result_text_scroll = ttk.Scrollbar(result_text_frame, orient="vertical", command=result_text.yview)
result_text_scroll.grid(row=0, column=1, sticky="ns")
result_text.configure(yscrollcommand=result_text_scroll.set)

# Function to insert text into the result_text widget
def insert_text(message):
    result_text.configure(state=tk.NORMAL)
    result_text.insert(tk.END, message)
    result_text.see(tk.END)
    result_text.configure(state=tk.DISABLED)

if os.path.exists('config.ini'):
    load_config()
    threading.Thread(target=auto_update, daemon=True).start()

root.mainloop()
