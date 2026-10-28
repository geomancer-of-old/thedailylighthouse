# config.py
# The Daily Lighthouse - application configuration
#
# NOTE (intentionally vulnerable lab): secrets live in source and the
# DB credentials here are deliberately reused by a system account so that
# a www-data webshell can pivot to SSH. Do not do this in real life.

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Weak, hardcoded session secret (predictable -> cookie forgery lesson)
SECRET_KEY = "lighthouse_dev_secret_2026"

# SQLite database path. The whole DB is a single file on disk; once a
# player has a webshell as www-data they can read/exfiltrate it directly.
DATABASE = os.path.join(BASE_DIR, "lighthouse.db")

# Where reporter "article images" are written. Served back by Flask with
# NO extension filtering (see routes.py) -> upload-to-RCE.
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

# Credentials that are (intentionally) reused by a Linux user named 'lprss'.
# Foothold -> read this file -> ssh lprss@target.
DB_SYSTEM_USER = "lprss"
DB_SYSTEM_PASS = "L1ghth0use_db_2026!"

# Checkpoint flag revealed once config is read via webshell/LFI.
FLAG_CONFIG = "FLAG{s3cr3ts_d0nt_b3l0ng_1n_s0urc3}"
