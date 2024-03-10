from math import log
import pytest
from dotenv import load_dotenv
import os
from supabase import Client, create_client

import celery_workers.src.api.database as database
import logging

logging.basicConfig(level=logging.DEBUG)


os.environ["DOTENV_FILE"] = "tests/.env"
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
TEST_USERNAME = os.environ.get("TEST_USERNAME")
TEST_PASSWORD = os.environ.get("TEST_PASSWORD")


@pytest.fixture(scope="module")
def supabase_test_client():
    """
    Creates a Supabase test client
    """
    print("Creating Supabase test client...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase.auth.sign_in_with_password(
        credentials={"email": TEST_USERNAME, "password": TEST_PASSWORD}
    )
    yield supabase
    supabase.auth.sign_out()


def test_download_file(supabase_test_client):
    logging.debug("Testing download_file...")
    user_id: str = supabase_test_client.auth.get_user().user.id
    assert True == True
    database.download_file(
        f"{user_id}/ede10a8b-6acb-4782-8cbc-a063e4a858f4.pdf",
        supabase_test_client,
    )
    assert (
        os.path.exists(
            f"./resources/{user_id}/ede10a8b-6acb-4782-8cbc-a063e4a858f4.pdf"
        )
        == True
    )
