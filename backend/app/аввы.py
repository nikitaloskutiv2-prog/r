
import sqlite3
from pathlib import Path
from datetime import datetime
import shutil


DB_PATH = Path("backend/test.db")
BACKUP_PATH = Path("backend/test.db.cleanup.backup")


def main():
    print("=" * 50)
    print("MESSAGE REFERENCES CLEANUP")
    print("=" * 50)

    if not DB_PATH.exists():
        print(f"ERROR: Database not found: {DB_PATH}")
        return

    # ---------------------------------------------------------
    # BACKUP
    # ---------------------------------------------------------

    print(f"Database: {DB_PATH}")
    print(f"Creating backup: {BACKUP_PATH}")

    shutil.copy2(DB_PATH, BACKUP_PATH)

    print("Backup created.")
    print()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # -----------------------------------------------------
        # FOREIGN KEYS
        # -----------------------------------------------------

        cursor.execute("PRAGMA foreign_keys = ON")

        # -----------------------------------------------------
        # BEFORE
        # -----------------------------------------------------

        cursor.execute("SELECT COUNT(*) FROM messages")
        messages_before = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM message_deletions")
        deletions_before = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM message_reactions")
        reactions_before = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM pinned_messages")
        pins_before = cursor.fetchone()[0]

        print("BEFORE:")
        print(f"  messages:          {messages_before}")
        print(f"  message_deletions: {deletions_before}")
        print(f"  message_reactions: {reactions_before}")
        print(f"  pinned_messages:   {pins_before}")
        print()

        # -----------------------------------------------------
        # 1. DELETE ORPHAN MESSAGE DELETIONS
        # -----------------------------------------------------

        print("Cleaning message_deletions...")

        cursor.execute("""
            DELETE FROM message_deletions
            WHERE message_id NOT IN (
                SELECT id FROM messages
            )
        """)

        deleted_deletions = cursor.rowcount

        print(
            f"  Removed orphan message_deletions: "
            f"{deleted_deletions}"
        )

        # -----------------------------------------------------
        # 2. DELETE ORPHAN REACTIONS
        # -----------------------------------------------------

        print("Cleaning message_reactions...")

        cursor.execute("""
            DELETE FROM message_reactions
            WHERE message_id NOT IN (
                SELECT id FROM messages
            )
        """)

        deleted_reactions = cursor.rowcount

        print(
            f"  Removed orphan message_reactions: "
            f"{deleted_reactions}"
        )

        # -----------------------------------------------------
        # 3. DELETE ORPHAN PINNED MESSAGES
        # -----------------------------------------------------

        print("Cleaning pinned_messages...")

        cursor.execute("""
            DELETE FROM pinned_messages
            WHERE message_id NOT IN (
                SELECT id FROM messages
            )
        """)

        deleted_pins = cursor.rowcount

        print(
            f"  Removed orphan pinned_messages: "
            f"{deleted_pins}"
        )

        # -----------------------------------------------------
        # 4. FIX BROKEN reply_to_id
        #
        # Do NOT delete the actual message.
        # Just remove the invalid reply reference.
        # -----------------------------------------------------

        print("Checking reply_to_id references...")

        cursor.execute("""
            SELECT id, reply_to_id
            FROM messages
            WHERE reply_to_id IS NOT NULL
              AND reply_to_id NOT IN (
                  SELECT id FROM messages
              )
            ORDER BY id
        """)

        broken_replies = cursor.fetchall()

        print(
            f"  Broken reply references found: "
            f"{len(broken_replies)}"
        )

        if broken_replies:
            print("  Fixing:")

            for message_id, reply_to_id in broken_replies:
                print(
                    f"    message {message_id}: "
                    f"reply_to_id {reply_to_id} -> NULL"
                )

            cursor.execute("""
                UPDATE messages
                SET reply_to_id = NULL
                WHERE reply_to_id IS NOT NULL
                  AND reply_to_id NOT IN (
                      SELECT id FROM messages
                  )
            """)

        # -----------------------------------------------------
        # COMMIT
        # -----------------------------------------------------

        conn.commit()

        print()
        print("Cleanup committed successfully.")
        print()

        # -----------------------------------------------------
        # VERIFICATION
        # -----------------------------------------------------

        print("Running verification...")
        print()

        # Orphan deletions
        cursor.execute("""
            SELECT COUNT(*)
            FROM message_deletions
            WHERE message_id NOT IN (
                SELECT id FROM messages
            )
        """)

        orphan_deletions = cursor.fetchone()[0]

        # Orphan reactions
        cursor.execute("""
            SELECT COUNT(*)
            FROM message_reactions
            WHERE message_id NOT IN (
                SELECT id FROM messages
            )
        """)

        orphan_reactions = cursor.fetchone()[0]

        # Orphan pins
        cursor.execute("""
            SELECT COUNT(*)
            FROM pinned_messages
            WHERE message_id NOT IN (
                SELECT id FROM messages
            )
        """)

        orphan_pins = cursor.fetchone()[0]

        # Broken replies
        cursor.execute("""
            SELECT COUNT(*)
            FROM messages
            WHERE reply_to_id IS NOT NULL
              AND reply_to_id NOT IN (
                  SELECT id FROM messages
              )
        """)

        broken_replies_after = cursor.fetchone()[0]

        # Message count
        cursor.execute("""
            SELECT COUNT(*)
            FROM messages
        """)

        messages_after = cursor.fetchone()[0]

        # MAX ID
        cursor.execute("""
            SELECT MAX(id)
            FROM messages
        """)

        max_id = cursor.fetchone()[0]

        # sqlite_sequence
        cursor.execute("""
            SELECT seq
            FROM sqlite_sequence
            WHERE name = 'messages'
        """)

        sequence_row = cursor.fetchone()
        sequence_value = sequence_row[0] if sequence_row else None

        print("AFTER:")
        print(f"  messages:              {messages_after}")
        print(f"  MAX message.id:        {max_id}")
        print(f"  sqlite_sequence:       {sequence_value}")
        print()
        print(f"  orphan deletions:      {orphan_deletions}")
        print(f"  orphan reactions:      {orphan_reactions}")
        print(f"  orphan pins:            {orphan_pins}")
        print(f"  broken reply_to_id:    {broken_replies_after}")
        print()

        # -----------------------------------------------------
        # FOREIGN KEY CHECK
        # -----------------------------------------------------

        print("Running PRAGMA foreign_key_check...")

        cursor.execute("""
            PRAGMA foreign_key_check
        """)

        fk_errors = cursor.fetchall()

        if fk_errors:
            print()
            print("WARNING: Foreign key errors still exist:")

            for error in fk_errors:
                print(" ", error)

        else:
            print("OK: No foreign key errors.")

        # -----------------------------------------------------
        # FINAL RESULT
        # -----------------------------------------------------

        print()
        print("=" * 50)

        if not fk_errors:
            print("CLEANUP COMPLETED SUCCESSFULLY")
        else:
            print("CLEANUP COMPLETED WITH WARNINGS")

        print("=" * 50)

        print()
        print(f"Backup: {BACKUP_PATH}")
        print(f"Messages: {messages_after}")
        print(f"MAX ID: {max_id}")
        print(f"AUTOINCREMENT sequence: {sequence_value}")

    except Exception as e:
        conn.rollback()

        print()
        print("=" * 50)
        print("ERROR - ROLLBACK")
        print("=" * 50)
        print(e)

    finally:
        conn.close()


if __name__ == "__main__":
    main()

