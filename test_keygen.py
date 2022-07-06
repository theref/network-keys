import json
import os
from pathlib import Path

import pytest

from keygen import store, generate


@pytest.fixture(scope='module')
def test_filepath():
    filepath = Path('test_keygen.json')
    if filepath.exists():
        os.remove(filepath)
    yield filepath
    os.remove(filepath)


@pytest.fixture()
def entry_one():
    return 'one', {'a': 'b'}


@pytest.fixture()
def entry_two():
    return 'two', {'c': 'd'}


def test_json_file_create(test_filepath, entry_one):
    label, entry = entry_one
    store(label=label, universal_materials=entry, filepath=test_filepath)
    with open(test_filepath, 'r') as file:
        restored_data = json.loads(file.read())
        assert label in restored_data
        assert restored_data[label] == entry


def test_json_file_update(test_filepath, entry_one, entry_two):
    label_one, entry_one = entry_one
    label_two, entry_two = entry_two
    store(label=label_two, universal_materials=entry_two, filepath=test_filepath)
    with open(test_filepath, 'r') as file:
        raw_data = file.read()
        restored_data = json.loads(raw_data)
        assert label_one in restored_data
        assert restored_data[label_one] == entry_one
        assert label_two in restored_data
        assert restored_data[label_two] == entry_two


def test_generate():
    universal_materials = generate()
    expected_fields = {
        'treasure_map',
        'policy_public_key',
        'alice_verifying_key',
        'threshold',
        'shares',
        'bob_verifying_key',
        'bob_verifying_secret',
        'bob_encrypting_key',
        'bob_encrypting_secret',
        'nodes'
    }
    for field in expected_fields:
        assert field in universal_materials
