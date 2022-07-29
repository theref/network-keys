from keygen import generate, store
from datetime import date
import requests
import math

month = date.today().strftime("%Y-%m")

JSON_FILEPATH: str = f"schemes/{month}/network-keys.json"
DURATION: int = 86_400 * 365  # seconds
DOMAIN = "mainnet"
TEACHER_NODE: str = "https://mainnet.nucypher.network:9151"

r = requests.get(f"{TEACHER_NODE}/status?json=true", verify=False).json()
num_nodes = r["fleet_state"]["population"]
unverified_nodes = [
    n
    for n in r["known_nodes"]
    if n["verified"] == False
    or n["recorded_fleet_state"]["checksum"] != r["fleet_state"]["checksum"]
]


num_available_nodes = num_nodes - len(unverified_nodes)

print(unverified_nodes)
print(num_available_nodes)


def get_majority_limit(total):
    return math.floor((total + 2) / 2)


SCHEMES = [
    (3, 5),
    (11, 20)
    # (51, 100),
    # (get_majority_limit(num_available_nodes), num_available_nodes),
]

for threshold, shares in SCHEMES:
    label = f"{threshold}-of-{shares}-{DOMAIN}"
    universal_materials = generate(
        threshold, shares, DOMAIN, [TEACHER_NODE], DURATION, label
    )
    store(label=label, filepath=JSON_FILEPATH, universal_materials=universal_materials)
