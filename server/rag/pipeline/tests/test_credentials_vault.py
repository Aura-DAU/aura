import pytest
from pipeline.ecampus import credentials_vault as vault


@pytest.fixture(autouse=True)
def clean_vault():
    """Each test gets a clean slate within the same temp DB file (set in
    conftest.py) — delete any rows the previous test left behind."""
    yield
    for erp_id in ("S1", "S2"):
        try:
            vault.unlink_credentials(erp_id)
        except Exception:
            pass
        for faculty_id in ("F1", "F2"):
            vault.revoke_advisor_consent(erp_id, faculty_id)


def test_store_and_retrieve_credentials_roundtrip():
    vault.store_credentials("S1", "s1_username", "s1_password")
    username, password = vault.get_credentials("S1")
    assert username == "s1_username"
    assert password == "s1_password"


def test_credentials_not_linked_raises_clear_error():
    with pytest.raises(vault.CredentialsNotLinked):
        vault.get_credentials("S_never_linked")


def test_is_linked_reflects_state():
    assert vault.is_linked("S2") is False
    vault.store_credentials("S2", "u", "p")
    assert vault.is_linked("S2") is True
    vault.unlink_credentials("S2")
    assert vault.is_linked("S2") is False


def test_storing_credentials_twice_overwrites_not_duplicates():
    vault.store_credentials("S1", "old_user", "old_pass")
    vault.store_credentials("S1", "new_user", "new_pass")
    username, password = vault.get_credentials("S1")
    assert (username, password) == ("new_user", "new_pass")


def test_credentials_are_actually_encrypted_at_rest():
    """Make sure we're not accidentally storing plaintext — read the raw
    DB row and confirm the password string doesn't appear in it."""
    import sqlite3
    vault.store_credentials("S1", "secretuser", "supersecretpassword123")
    conn = sqlite3.connect(vault.DB_PATH)
    row = conn.execute(
        "SELECT encrypted_blob FROM ecampus_credentials WHERE erp_id = ?", ("S1",)
    ).fetchone()
    conn.close()
    assert row is not None
    assert b"supersecretpassword123" not in row[0]


def test_advisor_consent_grant_and_check():
    assert vault.has_advisor_consent("S1", "F1") is False
    vault.grant_advisor_consent("S1", "F1")
    assert vault.has_advisor_consent("S1", "F1") is True


def test_advisor_consent_revoke():
    vault.grant_advisor_consent("S1", "F1")
    vault.revoke_advisor_consent("S1", "F1")
    assert vault.has_advisor_consent("S1", "F1") is False


def test_advisor_consent_is_scoped_per_faculty_member():
    """Granting access to F1 must not implicitly grant it to F2."""
    vault.grant_advisor_consent("S1", "F1")
    assert vault.has_advisor_consent("S1", "F1") is True
    assert vault.has_advisor_consent("S1", "F2") is False


def test_list_consented_faculty():
    vault.grant_advisor_consent("S1", "F1")
    vault.grant_advisor_consent("S1", "F2")
    shared_with = vault.list_consented_faculty("S1")
    assert set(shared_with) == {"F1", "F2"}


def test_list_consenting_students():
    vault.grant_advisor_consent("S1", "F1")
    vault.grant_advisor_consent("S2", "F1")
    students = vault.list_consenting_students("F1")
    assert set(students) == {"S1", "S2"}
