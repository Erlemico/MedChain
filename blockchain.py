import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List


# Utility: convert an object to a canonical JSON string (stable key order + no extra spaces)
# so hashing is deterministic and consistent.
def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


# Compute SHA-256 for a block using a canonical payload that binds:
# block_id + timestamp + data + prev_hash. Any change in these fields must change the hash.
def create_hash(block: Dict[str, Any]) -> str:
    payload = {
        "block_id": block.get("block_id"),
        "timestamp": block.get("timestamp", ""),
        "data": block.get("data", {}),
        "prev_hash": block.get("prev_hash"),
    }
    canonical_str = _canonical(payload)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


# Add a new block to the local chain:
# - auto-increment block_id
# - generate UTC timestamp
# - set prev_hash from the previous block's current_hash (or None for the first block)
# - compute current_hash and append to the chain
def add_block(chain: List[Dict[str, Any]], data: Dict[str, Any]) -> Dict[str, Any]:
    prev_hash = chain[-1]["current_hash"] if chain else None
    block_id = (chain[-1].get("block_id", 0) + 1) if chain else 1

    block = {
        "block_id": block_id,
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "data": {
            "patient_id": data.get("patient_id"),
            "clinic_name": data.get("clinic_name"),
            "diagnosis": data.get("diagnosis"),
            "treatment": data.get("treatment"),
            "date": data.get("date"),
            "doctor": data.get("doctor"),
        },
        "prev_hash": prev_hash,
    }

    block["current_hash"] = create_hash(block)
    chain.append(block)
    return block


# Verify the blockchain integrity:
# (1) Recompute each block hash and compare with stored current_hash (detects tampering)
# (2) Validate linkage: prev_hash must match the previous block's current_hash
def verify_chain(chain: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not chain:
        return {"valid": False, "message": "Empty chain"}

    for i, cur in enumerate(chain):
        expected_hash = create_hash(cur)
        if cur.get("current_hash") != expected_hash:
            return {
                "valid": False,
                "message": f"Hash mismatch at block_id={cur.get('block_id')} (index {i})"
            }

        if i > 0:
            prev = chain[i - 1]
            if cur.get("prev_hash") != prev.get("current_hash"):
                return {
                    "valid": False,
                    "message": f"Broken linkage at block_id={cur.get('block_id')} (index {i})"
                }

    return {"valid": True, "message": "Blockchain is valid!"}
