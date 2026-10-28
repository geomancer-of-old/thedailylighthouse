# db.py
# Database helpers + seed data for The Daily Lighthouse (lab target).

import sqlite3
import os
from config import DATABASE


def get_db():
    """Open a connection with row access by column name."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    # WAL reduces 'database is locked' under the small concurrency of a class.
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db():
    """Create tables and seed content. Safe to re-run (drops + recreates)."""
    conn = get_db()
    c = conn.cursor()

    c.executescript(
        """
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS articles;

        CREATE TABLE users (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT UNIQUE NOT NULL,
            password  TEXT NOT NULL,          -- plaintext on purpose (lesson)
            role      TEXT NOT NULL DEFAULT 'subscriber'
        );

        CREATE TABLE articles (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT NOT NULL,
            author     TEXT NOT NULL,
            body       TEXT NOT NULL,
            category   TEXT DEFAULT 'Home',
            published  INTEGER NOT NULL DEFAULT 1,  -- 0 = draft (IDOR target)
            created_at TEXT DEFAULT (datetime('now'))
        );
        """
    )

    # --- Users -----------------------------------------------------------
    
    users = [
        ("admin",   "Str0ngAdm1nP@ss_x92",  "admin"),
        ("editor",  "truthseeker99",        "reporter"),
        ("rsmith",  "password1",            "reporter"),
        ("reader1", "hunter2",              "subscriber"),
    ]
    c.executemany(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)", users
    )

    # --- Articles --------------------------------------------------------
    published = [
        ("Operation Greenwood: A Plot Against His Own People",
         "K. Kgodumo",
         "Declassified cabinet minutes from the Republic of Veltoria reveal that President Aldric Venn personally proposed Operation Greenwood, a scheme to manufacture terror on home soil and pin it on the neighbouring state of Kaldoria."
         "Under the plan, Veltorian operatives would hijack domestic airliners, detonate bombs in a coastal market, and sink a decommissioned naval vessel, each act dressed up as Kaldorian aggression."
         "Planners even drafted fake passenger manifests and pre-written Kaldorian “claims of responsibility” to be released to the press within the hour."
         "The goal was simple: a wave of public fury loud enough to justify a full invasion of Kaldorias eastern provinces."
         "Senior officers reportedly balked, and the file was buried for thirty years. Historians now call Greenwood one of the clearest examples of a government willing to attack its own citizens to win a war.",
         "Leaks", 1),

        ("Rationing Algorithms Found to be Rigged", "T. Matanda",
         "Internal memos obtained by our reporters reveal that the central food "
         "rationing algorithms explicitly prioritize Inner Party members while "
         "systematically starving outer sectors.", "Ministry Watch", 1),

        ("The Truth Behind 'Re-education' Centers", "J. Doe",
         "Whistleblowers from inside the walls share harrowing, uncensored "
         "accounts of what actually happens when dissidents disappear into "
         "state custody.", "Leaks", 1),

        ("New Tool Bypasses the Great Firewall", "Cipher",
         "A group of underground developers has successfully released a "
         "decentralized protocol allowing citizens to access unrestricted, "
         "non-state-approved media.", "Technology", 1),

         ("National Minerals Stolen.", "Anonymous",
         "For decades the overthrow of former President Maren Sol was blamed on domestic unrest."
         "Leaked cables tell a different story: foreign intelligence services, acting for a mining consortium, orchestrated the coup. "
         "The country sits atop vast reserves of gold and platinum and controls a trade corridor the Southern African region dependeds on."
         "Agents funded opposition militias, fed fabricated corruption stories to the international press, and bought the loyalty of two army generals."
         "Within weeks the republic was deposed and a pliant council signed away mineral rights for a generation", "Leaks", 1)
    ]

    
    drafts = [
        ("DRAFT: Identity of 'Anonymous Contributor' Revealed", "editor",
         "Reporter notes -- DO NOT PUBLISH. The source for the surveillance "
         "leak is Ministry sysadmin K. Okonkwo. Contact via secure drop only. "
         "FLAG{idor_expos3d_th3_unpublish3d_draft}", "Leaks", 0),
        ("DRAFT: Server Migration Notes", "admin",
         "Ops memo: the new box reuses the DB service account for SSH. "
         "Rotate before go-live. (We did not rotate.)", "Technology", 0),
    ]

    c.executemany(
        "INSERT INTO articles (title, author, body, category, published) "
        "VALUES (?, ?, ?, ?, ?)", published + drafts
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Initialized {DATABASE}")
