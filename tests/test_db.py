import unittest
from app import db


class DBTestCase(unittest.TestCase):
    def test_count_assigned_numbers(self):
        count = db.count_assigned_numbers()
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 0)

    def test_run_query_insert_and_select(self):
        # Inserta y selecciona un valor temporal en purchases (no afecta producción si rollback)
        import uuid
        invoice_id = f"test_{uuid.uuid4().hex[:8]}"
        db.run_query("INSERT INTO purchases (invoice_id, amount, email, numbers, status) VALUES (%s, %s, %s, %s, 'confirmed')", params=(invoice_id, 12345, 'test@demo.com', '1,2,3'), commit=True)
        row = db.run_query("SELECT * FROM purchases WHERE invoice_id = %s", params=(invoice_id,), fetchone=True)
        self.assertIsNotNone(row)
        # Limpieza
        db.run_query("DELETE FROM purchases WHERE invoice_id = %s", params=(invoice_id,), commit=True)


if __name__ == '__main__':
    unittest.main()
import unittest
from app import db

class DBTestCase(unittest.TestCase):
    def test_count_assigned_numbers(self):
        count = db.count_assigned_numbers()
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 0)

    def test_run_query_insert_and_select(self):
        # Inserta y selecciona un valor temporal en purchases (no afecta producción si rollback)
        import uuid
        invoice_id = f"test_{uuid.uuid4().hex[:8]}"
        db.run_query("INSERT INTO purchases (invoice_id, amount, email, numbers, status) VALUES (%s, %s, %s, %s, 'confirmed')", params=(invoice_id, 12345, 'test@demo.com', '1,2,3'), commit=True)
        row = db.run_query("SELECT * FROM purchases WHERE invoice_id = %s", params=(invoice_id,), fetchone=True)
        self.assertIsNotNone(row)
        # Limpieza
        db.run_query("DELETE FROM purchases WHERE invoice_id = %s", params=(invoice_id,), commit=True)

if __name__ == '__main__':
    unittest.main()
