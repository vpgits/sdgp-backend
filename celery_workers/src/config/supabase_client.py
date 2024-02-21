import os
import logging
from supabase import Client
from supabase import create_client


def get_supabase_client(access_token: str, refresh_token: str) -> Client:
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    key1 = os.environ.get("SUPABASE_KEY")

    supabase: Client = create_client(url, key1)
    supabase.auth.set_session(access_token=access_token, refresh_token=refresh_token)
    return supabase


def get_current_user(supabase_client: Client, access_token: str) -> str:
    user = supabase_client.auth.get_user(access_token)
    if user is None:
        raise ValueError("User is not logged in.")
    return user.user.id
