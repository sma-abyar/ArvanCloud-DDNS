import requests
import tkinter as tk
from tkinter import messagebox
import threading
import time
import configparser
import os


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

# def check_ip(ip, last_ip):
#     if ip == last_ip:
        
def check_dns_record(api_key, record_name, domain, record_id):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': api_key
    }
    response = requests.get(f"https://napi.arvancloud.ir/cdn/4.0/domains/{domain}/dns-records/{record_id}", headers=headers)
    if response.status_code == 200:
        records = response.json()
        for record in records["data"]:
            if record["name"] == record_name:
                ip_address = record["value"][0]["ip"]
                return ip_address  # Return the IP address of the DNS record
                break
    return None


def update_dns_record():
    api_key = api_key_entry.get()
    record_name = record_name_entry.get()
    domain = domain_entry.get()
    record_id = record_id_entry.get()
    record_type = record_type_entry.get()
    content = ip_label.cget("text")

    record_id = record_id.strip()  # Removing leading/trailing whitespace
    # dns_record_ip = check_dns_record(api_key, record_name, domain, record_id)
    
    # if dns_record_ip == content:
    #     result_text.insert(tk.END, f"Info: The IP address already matches the A record for {record_id}.\n")

    # elif dns_record_ip is None:
    #     result_text.insert(tk.END, f"Error: Could not retrieve the DNS record for {record_id}.\n")

    headers = {
        'Content-Type': 'application/json',
        'Authorization': api_key
    }

    data = {
        "value": [
            {
                "ip": content,
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
            last_ip = content
        else:
            result_text.insert(tk.END, f"Error: Failed to update DNS record for {record_name}: {response.text}\n")
    except requests.RequestException as e:
        result_text.insert(tk.END, f"API request failed for {record_name}: {e}\n")


def auto_update():
    global auto_update_flag
    auto_update_flag = True
    interval = float(interval_entry.get()) * 60  # Convert minutes to seconds
    while auto_update_flag:
        for remaining in range(int(interval), 0, -1):
            mins, secs = divmod(remaining, 60)
            countdown_label.config(text=f"Next check in: {mins:02d}:{secs:02d}")
            root.update()
            time.sleep(1)
            if not auto_update_flag:
                break

        if auto_update_flag:
            current_ip = get_public_ip()
            ip_label.config(text=current_ip)  # Update the IP label with the current IP
            # update_performed = False
            record_id = record_id.strip()
            # dns_record_ip = check_dns_record(api_key_entry.get(), domain_entry.get(), record_id)
            # if current_ip != dns_record_ip:
            update_dns_record()
            # update_performed = True
            # if not update_performed:
                # result_text.insert(tk.END, f"No update necessary at {time.strftime('%Y-%m-%d %H:%M:%S')}.\n")
        countdown_label.config(text="Update check completed.")


def stop_auto_update():
    global auto_update_flag
    auto_update_flag = False

# GUI Setup
root = tk.Tk()
root.title("Arvan DNS Updater")

# Public IP Display
tk.Label(root, text="Your Public IP:").pack()
ip_label = tk.Label(root, text=get_public_ip())
ip_label.pack()

# Save and Load Buttons
save_config_button = tk.Button(root, text="Save Config", command=save_config)
save_config_button.pack()

load_config_button = tk.Button(root, text="Load Config", command=load_config)
load_config_button.pack()

# Input Fields with Labels
tk.Label(root, text="API Key:").pack()
api_key_entry = tk.Entry(root)
api_key_entry.pack()

tk.Label(root, text="Record Name:").pack()
record_name_entry = tk.Entry(root)
record_name_entry.pack()

tk.Label(root, text="Domain:").pack()
domain_entry = tk.Entry(root)
domain_entry.pack()

tk.Label(root, text="Record ID:").pack()
record_id_entry = tk.Entry(root)
record_id_entry.pack()

tk.Label(root, text="Record Type:").pack()
record_type_entry = tk.Entry(root)
record_type_entry.pack()

# Update Button
update_button = tk.Button(root, text="Update DNS Record", command=update_dns_record)
update_button.pack()

# Interval Input Field
tk.Label(root, text="Update Interval (minutes):").pack()
interval_entry = tk.Entry(root)
interval_entry.pack()

# Start and Stop Auto-Update Buttons
start_auto_update_button = tk.Button(root, text="Start Auto Update", command=lambda: threading.Thread(target=auto_update, daemon=True).start())
start_auto_update_button.pack()

stop_auto_update_button = tk.Button(root, text="Stop Auto Update", command=stop_auto_update)
stop_auto_update_button.pack()

# Result Text Widget
result_text = tk.Text(root, height=5, width=50)
result_text.pack()

# Countdown timer
countdown_label = tk.Label(root, text="Next check in: --:--")
countdown_label.pack()

def start_auto_update_thread():
    threading.Thread(target=auto_update, daemon=True).start()

# Check for config.ini and load if exists
if os.path.exists('config.ini'):
    load_config()
    start_auto_update_thread()

root.mainloop()
