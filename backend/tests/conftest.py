"""Deterministic test configuration loaded before application modules."""
import os


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["AI_PROVIDER"] = "local"
