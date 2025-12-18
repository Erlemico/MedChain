import requests
from flask import Flask, request, jsonify

from blockchain import add_block
from storage import load_blockchain, save_blockchain

app = Flask(__name__)

# =========================
# LOAD BLOCKCHAIN (PERSISTENT)
# =========================
blockchain = load_blockchain()

# =========================
# HOME
# =========================
@app.route('/')
def home():
    return "Welcome to MedChain - Modular Blockchain Integrity Layer"

# =========================
# ADD DATA (POST)
# =========================
@app.route('/add_data', methods=['POST'])
def add_data():
    data = request.json

    # Tambah block ke blockchain lokal
    new_block = add_block(blockchain, data)

    # Simpan ke file (persistent)
    save_blockchain(blockchain)

    # Kirim ke Google Sheets (cloud display)
    google_script_url = (
        'https://script.google.com/macros/s/AKfycbymjuLCvAnodct1kb7erxg6JjOKo_UMtij16_qVQyKGQ-F0MI3Sic7SGfoQta3P1Ryi/exec'
    )

    try:
        requests.post(
            google_script_url,
            json=new_block,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
    except Exception as e:
        return jsonify({
            'message': 'Block added, but failed to send to Google Sheets',
            'error': str(e)
        }), 201

    return jsonify(new_block), 201

# =========================
# GET FULL BLOCKCHAIN
# =========================
@app.route('/get_chain', methods=['GET'])
def get_chain():
    return jsonify({
        'length': len(blockchain),
        'chain': blockchain
    }), 200

# =========================
# VERIFY FULL BLOCKCHAIN
# =========================
@app.route('/verify_chain', methods=['GET'])
def verify_chain():
    for i in range(1, len(blockchain)):
        prev_block = blockchain[i - 1]
        current_block = blockchain[i]

        if current_block['prev_hash'] != prev_block['current_hash']:
            return jsonify({
                'status': 'INVALID',
                'message': f'Blockchain is tampered at block {current_block["block_id"]}'
            }), 400

    return jsonify({
        'status': 'VALID',
        'message': 'Blockchain is valid'
    }), 200

# =========================
# VERIFY SINGLE BLOCK (BY ID)
# =========================
@app.route('/verify_chain/<int:block_id>', methods=['GET'])
def verify_block(block_id):

    block = next((b for b in blockchain if b['block_id'] == block_id), None)

    if not block:
        return jsonify({'message': 'Block not found'}), 404

    # Genesis block
    if block_id == 1:
        if block['prev_hash'] is None:
            return jsonify({'message': 'Genesis block is valid'}), 200
        else:
            return jsonify({'message': 'Genesis block is tampered'}), 400

    prev_block = next((b for b in blockchain if b['block_id'] == block_id - 1), None)

    if not prev_block:
        return jsonify({'message': 'Previous block not found'}), 400

    if block['prev_hash'] != prev_block['current_hash']:
        return jsonify({
            'message': f'Blockchain is tampered at block {block_id}'
        }), 400

    return jsonify({
        'message': f'Block {block_id} is valid'
    }), 200

# =========================
# RUN APP
# =========================
if __name__ == '__main__':
    app.run(debug=True)
