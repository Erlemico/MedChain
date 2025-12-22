import json
import os

BLOCKCHAIN_FILE = 'blockchain.json'

def load_blockchain():
    if not os.path.exists(BLOCKCHAIN_FILE):
        return []
    with open(BLOCKCHAIN_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_blockchain(blockchain):
    with open(BLOCKCHAIN_FILE, 'w', encoding='utf-8') as f:
        json.dump(blockchain, f, indent=4, ensure_ascii=False)
