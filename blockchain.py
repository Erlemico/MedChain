import hashlib
from datetime import datetime

# Fungsi untuk membuat hash
def create_hash(block_data):
    block_str = f"{block_data['block_id']}{block_data['patient_id']}{block_data['date']}{block_data['diagnosis']}{block_data.get('prev_hash', '')}"
    return hashlib.sha256(block_str.encode()).hexdigest()

# Fungsi untuk menambahkan blok baru ke blockchain
def add_block(chain, block_data):
    prev_hash = chain[-1]['current_hash'] if chain else None  # Mengambil current_hash dari blok sebelumnya
    current_hash = create_hash(block_data)  # Membuat current_hash untuk blok baru
    new_block = {
        'block_id': block_data['block_id'],
        'patient_id': block_data['patient_id'],
        'clinic_name': block_data['clinic_name'],
        'diagnosis': block_data['diagnosis'],
        'treatment': block_data['treatment'],
        'date': block_data['date'],
        'doctor': block_data['doctor'],
        'prev_hash': prev_hash,  # Menyimpan prev_hash dari blok sebelumnya
        'current_hash': current_hash  # Menyimpan current_hash untuk blok baru
    }
    chain.append(new_block)
    return new_block

# Fungsi untuk memverifikasi blockchain
def verify_chain(chain):
    for i in range(1, len(chain)):  # Mulai dari blok ke-2 untuk memverifikasi chain
        if chain[i]['prev_hash'] != chain[i - 1]['current_hash']:  # Cek apakah prev_hash sesuai dengan current_hash blok sebelumnya
            return {'message': 'Blockchain is tampered!'}  # Blockchain sudah dimodifikasi
    return {'message': 'Blockchain is valid!'}  # Blockchain tidak dimodifikasi
