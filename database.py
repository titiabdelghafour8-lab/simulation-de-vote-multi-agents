import sqlite3
import os

class DatabaseManager:
    """Manages the SQLite database for the election simulation."""
    def __init__(self, db_name="election.db"):
        self.db_name = db_name
        self.create_tables()

    def create_tables(self):
        """Creates the necessary tables if they don't exist."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                voter_id TEXT,
                persona TEXT,
                rank_1 TEXT,
                rank_2 TEXT,
                rank_3 TEXT,
                reasoning TEXT,
                confidence INTEGER,
                round_num INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def save_vote(self, run_id, voter_id, persona, ranked_candidates, reasoning, confidence, round_num):
        """Saves a single vote record to the database."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Ensure we have exactly 3 rankings, pad with None if necessary
        r1 = ranked_candidates[0] if len(ranked_candidates) > 0 else None
        r2 = ranked_candidates[1] if len(ranked_candidates) > 1 else None
        r3 = ranked_candidates[2] if len(ranked_candidates) > 2 else None
        
        cursor.execute('''
            INSERT INTO votes (run_id, voter_id, persona, rank_1, rank_2, rank_3, reasoning, confidence, round_num)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (run_id, voter_id, persona, r1, r2, r3, reasoning, confidence, round_num))
        conn.commit()
        conn.close()