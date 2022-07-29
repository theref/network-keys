#!/usr/bin/env python

import json
from pathlib import Path
from typing import Dict, List

import click
from eth_utils import to_checksum_address
from nucypher.characters.lawful import Bob, Alice, Ursula
from nucypher_core.umbral import SecretKey

from nucypher.policy.reservoir import PrefetchStrategy


def store(label: str, universal_materials: Dict[str, str], filepath: str) -> None:
    filepath = Path(filepath)
    if filepath.parent.exists() == False:
        filepath.parent.mkdir()
    filepath.touch(exist_ok=True)
    entry = {label: universal_materials}
    with open(filepath, 'r+') as file:
        data = file.read() or str({})
        data = json.loads(data)
        data.update(entry)
        data = json.dumps(data, indent=4)
        file.seek(0)
        written = file.write(data)
    click.secho(f'Generated JSON output; Wrote {written} bytes to {filepath}', fg='green')


def generate(threshold: int, shares: int, domain: str, nodes: List[str], duration: int, label: str) -> Dict[str, str]:

    # Universal Bob
    bob_verifying_secret = SecretKey.random()
    bob_verifying_key = bob_verifying_secret.public_key()
    bob_decrypting_secret = SecretKey.random()
    bob_decrypting_key = bob_decrypting_secret.public_key()
    universal_bob = Bob.from_public_keys(verifying_key=bob_verifying_key,
                                         encrypting_key=bob_decrypting_key,
                                         federated_only=True)
    click.secho(f'Generated Universal Bob {bytes(universal_bob.stamp).hex()}', fg='cyan')

    # collect ursulas for this universal policy
    ursulas = {Ursula.from_teacher_uri(teacher_uri=uri, federated_only=True, min_stake=0) for uri in nodes}

    # Universal Alice
    alice = Alice(federated_only=True, domain=domain, known_nodes=ursulas)
    click.secho(f'Generated Universal Alice {bytes(universal_bob.stamp).hex()}', fg='cyan')
    alice.start_learning_loop(now=True)

    # Network Policy
    click.secho('peering and sampling...', fg='yellow')
    policy = alice.grant(bob=universal_bob,
                         ursulas=ursulas,
                         label=label.encode(),
                         threshold=threshold,
                         shares=shares,
                         duration=duration)
    click.secho(f'Generated Network Policy '
                f'"{label}" with M({threshold}) of N({shares}) {bytes(policy.public_key).hex()}',
                fg='green')

    # ensure Bob can decrypt the treasure map
    decrypted_treasure_map = policy.treasure_map.decrypt(
        bob_decrypting_secret,
        publisher_verifying_key=alice.stamp.as_umbral_pubkey()
    )
    node_addresses = [to_checksum_address(addr) for addr in decrypted_treasure_map.destinations]

    # Export
    payload = {

        # policy
        'treasure_map': bytes(policy.treasure_map).hex(),
        'policy_public_key': bytes(policy.public_key).hex(),
        'threshold': threshold,
        'shares': shares,

        # alice
        'alice_verifying_key': bytes(alice.stamp).hex(),
        # TODO: store Alice's secret?

        # bob
        'bob_verifying_key': bytes(bob_verifying_key).hex(),
        'bob_verifying_secret': bob_verifying_secret.to_secret_bytes().hex(),
        'bob_encrypting_key': bytes(bob_decrypting_key).hex(),
        'bob_encrypting_secret': bob_decrypting_secret.to_secret_bytes().hex(),

        # ursulas
        'domain': domain,
        'nodes': node_addresses

    }
    return payload


#
# Config
#

JSON_FILEPATH: str = 'network-keys.json'
THRESHOLD: int = 2
SHARES: int = 3
DURATION: int = 86_400 * 365  # seconds
DOMAIN = 'ibex'
NODES: List[str] = [
    # "https://ibex.nucypher.network:9151",
    # "https://143.198.239.218:9151"  # james testnet
]
LABEL: str = f'{THRESHOLD}-of-{SHARES}-{DOMAIN}'

if __name__ == '__main__':
    universal_materials = generate(THRESHOLD, SHARES, DOMAIN, NODES, DURATION, LABEL)
    store(
        label=LABEL,
        filepath=JSON_FILEPATH,
        universal_materials = universal_materials,
    )
    click.secho('Done')
