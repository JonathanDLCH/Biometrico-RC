import unittest
from sqlalchemy import create_engine, text
from config.settings import DATABASE_URL


class TestDatabaseConnection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.database_url = DATABASE_URL
        if not cls.database_url:
            raise unittest.SkipTest(
                "DATABASE_URL no configurada. Define DATABASE_URL o DB_USER/DB_PASSWORD/DB_HOST/DB_PORT/DB_NAME en .env."
            )

    def test_database_url_is_mysql(self):
        self.assertTrue(
            self.database_url.startswith("mysql+pymysql://"),
            "DATABASE_URL debe usar el driver MySQL/PyMySQL y comenzar con mysql+pymysql://"
        )

    def test_can_connect_to_database(self):
        engine = create_engine(self.database_url, pool_pre_ping=True, future=True)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            self.assertEqual(result.scalar_one(), 1)


if __name__ == "__main__":
    unittest.main()
