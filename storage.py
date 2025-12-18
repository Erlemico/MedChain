import json
import os

BLOCKCHAIN_FILE = 'blockchain.json'

def load_blockchain():
    if not os.path.exists(BLOCKCHAIN_FILE):
        return []
    with open(BLOCKCHAIN_FILE, 'r') as f:
        return json.load(f)

def save_blockchain(blockchain):
    with open(BLOCKCHAIN_FILE, 'w') as f:
        json.dump(blockchain, f, indent=4)

