import requests

url = "https://api.strata.paloaltonetworks.com/config/objects/v1/addresses"
token = "your_access_token_here"

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {token}"
}

objects = [
  {"name":"Internal_1","folder":"Azure-SEE","ip_netmask":"10.10.10.1/32"},
  {"name":"Internal_2","folder":"Azure-SEE","ip_netmask":"10.10.10.2/32"},
  {"name":"Internal_3","folder":"Azure-SEE","ip_netmask":"10.10.10.3/32"},
  {"name":"Internal_4","folder":"Azure-SEE","ip_netmask":"10.10.10.4/32"}
]

for obj in objects:
    payload = {
        "name": obj["name"],
        "folder": obj["folder"],
        "ip_netmask": obj["ip_netmask"]
    }

    r = requests.post(url, json=payload, headers=headers)
    print(obj["name"], r.status_code, r.text)