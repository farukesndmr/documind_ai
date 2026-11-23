import os
import sys
from pathlib import Path

# Testler gerçek servislere bağlanmaz; ayarların yüklenebilmesi için sahte değerler.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
