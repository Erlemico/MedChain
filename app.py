import requests
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify

from blockchain import add_block, verify_chain, create_hash
from storage import load_blockchain, save_blockchain

app = Flask(__name__)

# LOAD BLOCKCHAIN (PERSISTENT)
blockchain = load_blockchain()

# Google Apps Script (Cloud display / cloud chain source)
GOOGLE_SCRIPT_URL = (
    "https://script.google.com/macros/s/AKfycbyuovI6kwwBol4YG8MMv6NvH0s6UTmFNqECHVSdO5GFL4eg-jHgqFrSd19eoUe6aNT2/exec"
)

REQUIRED_FIELDS = ["patient_id", "clinic_name", "diagnosis", "treatment", "date", "doctor"]

# Use Asia/Jakarta timezone (+07:00) for normalizing ISO Z time from Apps Script
JAKARTA_TZ = timezone(timedelta(hours=7))


# HELPERS
def validate_request_payload(data: dict):
    if not isinstance(data, dict):
        return False, "Request body harus JSON object."
    missing = [k for k in REQUIRED_FIELDS if k not in data or data[k] in (None, "")]
    if missing:
        return False, f"Field wajib kurang: {', '.join(missing)}"
    return True, ""


def fetch_cloud_chain(script_url: str):
    """
    Expect Apps Script supports:
      GET ?action=get_chain -> JSON array of blocks
    """
    try:
        r = requests.get(script_url, params={"action": "get_chain"}, timeout=8)
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _to_int(x):
    try:
        return int(x)
    except Exception:
        return x


def normalize_datetime(v):
    """
    Normalize date/time returned by Apps Script (often ISO '...Z') into:
      'YYYY-MM-DD HH:MM:SS' in Asia/Jakarta time.
    If parsing fails, return original string.
    """
    if v is None:
        return ""
    s = str(v).strip()
    if not s:
        return ""

    # Convert ISO (e.g., 2025-12-11T03:00:00.000Z / 2025-12-11T03:00:00Z)
    if "T" in s:
        try:
            iso = s
            if iso.endswith("Z"):
                iso = iso.replace("Z", "+00:00")
            dt = datetime.fromisoformat(iso)
            if dt.tzinfo is None:
                return s
            dt_local = dt.astimezone(JAKARTA_TZ)
            return dt_local.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return s

    # Already local-like string (e.g., "2025-12-11 10:00:00") -> keep
    return s


def normalize_for_compare(block: dict) -> dict:
    """
    Build a comparable view of a block (local vs cloud) focusing on meaningful fields.
    This avoids false differences due to date formatting.
    """
    d = block.get("data") or {}
    return {
        "block_id": _to_int(block.get("block_id")),
        "timestamp": block.get("timestamp", ""),
        "patient_id": d.get("patient_id"),
        "clinic_name": d.get("clinic_name"),
        "diagnosis": d.get("diagnosis"),
        "treatment": d.get("treatment"),
        "date": normalize_datetime(d.get("date")),
        "doctor": d.get("doctor"),
        "prev_hash": block.get("prev_hash"),
    }


def build_block_for_hash(block: dict) -> dict:
    """
    Build a block object (without current_hash) to recompute expected hash.
    We normalize the 'date' field so the recomputed hash matches the local chain
    even if Apps Script returns ISO Z values.
    """
    d = block.get("data") or {}
    return {
        "block_id": _to_int(block.get("block_id")),
        "timestamp": block.get("timestamp", ""),
        "data": {
            "patient_id": d.get("patient_id"),
            "clinic_name": d.get("clinic_name"),
            "diagnosis": d.get("diagnosis"),
            "treatment": d.get("treatment"),
            "date": normalize_datetime(d.get("date")),
            "doctor": d.get("doctor"),
        },
        "prev_hash": block.get("prev_hash"),
    }


# HOME
@app.route("/", methods=["GET"])
def home():
    return "Welcome to MedChain - Modular Blockchain Integrity Layer"


# ADD DATA (POST)
@app.route("/add_data", methods=["POST"])
def add_data():
    global blockchain

    data = request.get_json(silent=True)
    ok, err = validate_request_payload(data)
    if not ok:
        return jsonify({"status": "error", "message": err}), 400

    # Add block to local blockchain
    new_block = add_block(blockchain, data)

    # Persist to file
    save_blockchain(blockchain)

    # Send to Google Apps Script (cloud display)
    cloud_info = None
    try:
        resp = requests.post(
            GOOGLE_SCRIPT_URL,
            json=new_block,
            headers={"Content-Type": "application/json"},
            timeout=8
        )

        cloud_info = {
            "status_code": resp.status_code,
            "ok": resp.ok
        }

        # Parse JSON response to avoid escaped string output
        try:
            cloud_info["response"] = resp.json()
        except ValueError:
            cloud_info["response_text"] = resp.text[:200]

    except requests.exceptions.Timeout:
        cloud_info = {"error": "timeout", "message": "Request to Google Apps Script timed out"}
    except requests.exceptions.RequestException as e:
        cloud_info = {"error": "request_error", "message": str(e)}
    except Exception as e:
        cloud_info = {"error": "unexpected_error", "message": str(e)}

    return jsonify({
        "status": "success",
        "block": new_block,
        "cloud": cloud_info
    }), 201


# GET BLOCKCHAIN
@app.route("/get_chain", methods=["GET"])
def get_chain():
    return jsonify({
        "length": len(blockchain),
        "chain": blockchain
    }), 200


# VERIFY BLOCKCHAIN
@app.route("/verify_chain", methods=["GET"])
def verify_full_chain():
    result = verify_chain(blockchain)
    status = 200 if result.get("valid") else 400
    return jsonify(result), status


# VERIFY SINGLE BLOCK (BY ID)
@app.route("/verify_chain/<int:block_id>", methods=["GET"])
def verify_block(block_id: int):
    idx = None
    for i, b in enumerate(blockchain):
        if _to_int(b.get("block_id")) == block_id:
            idx = i
            break

    if idx is None:
        return jsonify({"status": "error", "message": "Block not found"}), 404

    partial = verify_chain(blockchain[: idx + 1])
    if not partial.get("valid"):
        return jsonify({
            "status": "INVALID",
            "message": partial.get("message"),
            "block_id": block_id
        }), 400

    return jsonify({
        "status": "VALID",
        "message": f"Block {block_id} is valid",
        "block": blockchain[idx]
    }), 200


# DETECT CLOUD TAMPERING
@app.route("/detect_cloud_tampering", methods=["GET"])
def detect_cloud_tampering():
    local_verify = verify_chain(blockchain)
    cloud_chain = fetch_cloud_chain(GOOGLE_SCRIPT_URL)

    result = {
        "local": {
            "valid": local_verify.get("valid", False),
            "message": local_verify.get("message"),
            "length": len(blockchain),
            "last_hash": blockchain[-1].get("current_hash") if blockchain else None
        },
        "cloud": {
            "length": len(cloud_chain),
            "last_hash": cloud_chain[-1].get("current_hash") if cloud_chain else None
        },
        "tampering_detected": False,
        "divergence_index": None,
        "cloud_hash_mismatch": False,
        "diff_sample": None,
        "note": None
    }

    if not cloud_chain:
        result["note"] = (
            "Cloud chain cannot be retrieved / empty."
            "Ensure Apps Script supports GET with ?action=get_chain."
        )
        return jsonify(result), 200

    # (1) Detect content differences (local vs cloud)
    min_len = min(len(blockchain), len(cloud_chain))
    divergence = None
    diff_sample = None

    for i in range(min_len):
        lp = normalize_for_compare(blockchain[i])
        cp = normalize_for_compare(cloud_chain[i])

        if lp != cp and divergence is None:
            divergence = i
            diffs = {}
            for k in lp.keys():
                if lp.get(k) != cp.get(k):
                    diffs[k] = {"local": lp.get(k), "cloud": cp.get(k)}
            diff_sample = diffs

    # (2) Detect hash mismatch inside cloud (data edited but current_hash not updated)
    cloud_mismatch = False
    for b in cloud_chain:
        stored = b.get("current_hash", "")
        if not stored:
            continue

        expected = create_hash(build_block_for_hash(b))
        if stored != expected:
            cloud_mismatch = True
            break

    result["divergence_index"] = divergence
    result["diff_sample"] = diff_sample
    result["cloud_hash_mismatch"] = cloud_mismatch

    tampered = (
        (divergence is not None) or
        cloud_mismatch or
        (len(blockchain) != len(cloud_chain))
    )
    result["tampering_detected"] = tampered

    if tampered and divergence is None and len(blockchain) != len(cloud_chain):
        result["note"] = "Same prefix but different chain length (sync delay / mismatch)."

    return jsonify(result), 200


# RUN APP
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
