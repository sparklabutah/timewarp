import bisect
import hashlib
import json
import logging
import random
from os.path import dirname, abspath, join

BASE_DIR = dirname(abspath(__file__))
DEBUG_PROD_SIZE = None  # set to `None` to disable

DEFAULT_ATTR_PATH = join(BASE_DIR, '../data/items_ins_v2_1000.json')
DEFAULT_FILE_PATH = join(BASE_DIR, '../data/items_shuffle_1000.json')
DEFAULT_REVIEW_PATH = join(BASE_DIR, '../data/reviews.json')

FEAT_CONV = join(BASE_DIR, '../data/feat_conv.pt')
FEAT_IDS = join(BASE_DIR, '../data/feat_ids.pt')

HUMAN_ATTR_PATH = join(BASE_DIR, '../data/items_human_ins.json')
HUMAN_ATTR_PATH = join(BASE_DIR, '../data/items_human_ins.json')

def random_idx(cum_weights):
    """Generate random index by sampling uniformly from sum of all weights, then
    selecting the `min` between the position to keep the list sorted (via bisect)
    and the value of the second to last index
    """
    pos = random.uniform(0, cum_weights[-1])
    idx = bisect.bisect(cum_weights, pos)
    idx = min(idx, len(cum_weights) - 2)
    return idx

def setup_logger(session_id, user_log_dir):
    """Creates a log file and logging object for the corresponding session ID"""
    logger = logging.getLogger(session_id)
    formatter = logging.Formatter('%(message)s')
    file_handler = logging.FileHandler(
        user_log_dir / f'{session_id}.jsonl',
        mode='w'
    )
    file_handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    return logger

def generate_mturk_code(session_id: str) -> str:
    """Generates a redeem code corresponding to the session ID for an MTurk
    worker once the session is completed
    """
    sha = hashlib.sha1(session_id.encode())
    return sha.hexdigest()[:10].upper()

def generate_order_code(asin: str, options: dict) -> str:
    """Generates a unique access code for an order based on the product (ASIN) 
    and selected options (size, color, etc.).
    
    Same product with same options will always produce the same code.
    Different products or different options will produce different codes.
    
    Args:
        asin: The product ASIN identifier
        options: Dictionary of product options (e.g., {'color': 'red', 'size': 'large'})
    
    Returns:
        A unique 10-character uppercase code representing the product-option combination
    """
    # Normalize options: sort keys and values to ensure consistency
    # This ensures {'color': 'red', 'size': 'large'} produces the same hash
    # as {'size': 'large', 'color': 'red'}
    normalized_options = {}
    if options:
        # Sort by key, and normalize values (convert to lowercase, strip whitespace)
        for key in sorted(options.keys()):
            value = options[key]
            if isinstance(value, str):
                value = value.lower().strip()
            normalized_options[key.lower().strip()] = value
    
    # Create a deterministic string representation
    # Combine ASIN with sorted JSON representation of options
    options_str = json.dumps(normalized_options, sort_keys=True)
    combined = f"{asin}:{options_str}"
    
    # Generate hash
    sha = hashlib.sha1(combined.encode('utf-8'))
    return sha.hexdigest()[:10].upper()