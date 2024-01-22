import os
import time

from supabase import create_client
from supabase.client import ClientOptions
import logging


def get_supabase_client(access_token: str, refresh_token: str):
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    key1 = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("Supabase URL or Key is not set in environment variables.")

    supabase = create_client(url, key)
    return supabase
