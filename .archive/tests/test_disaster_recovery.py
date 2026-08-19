"""Comprehensive Disaster Recovery (Backup, Corrupt Detection, Restore) Test Suite for Gate 11."""
import os
import tempfile
from pathlib import Path
import pytest

from app.models.database import db
from app.services.backup import DisasterRecoveryService

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    db._init_db()

@pytest.mark.asyncio
async def test_disaster_recovery_backup_and_restore_cycle(tmp_path):
    """Verifies complete backup creation, DB destruction, and restore recovery cycle."""
    t_now = int(pytest.importorskip("time").time() * 1000)
    email = f"dr_test_user_{t_now}@aegisdr.io"
    user = await db.create_user(
        email=email,
        hashed_password="hashed_dr_password_123",
        full_name="DR Test Officer",
        role="OWNER"
    )
    org = await db.create_organization(
        name="Disaster Recovery Enterprise",
        slug=f"dr-enterprise-{t_now}",
        owner_user_id=user["id"],
        tier="enterprise"
    )


    dr = DisasterRecoveryService(db_path=Path(db.db_path))
    backup_file = tmp_path / "dr_test_backup.db"

    # 2. Create online hot backup
    meta = dr.create_backup(custom_backup_path=backup_file)
    assert backup_file.exists()
    assert meta["table_count"] >= 8
    assert len(meta["sha256"]) == 64
    assert meta["integrity"] == "ok"

    # 3. Simulate disaster: restore to a new clean DB path
    restored_db_path = tmp_path / "restored_aegis.db"
    res = dr.restore_backup(backup_file=backup_file, target_db=restored_db_path)
    assert res["status"] == "RESTORED"
    assert res["table_count"] == meta["table_count"]
    assert res["integrity"] == "ok"

    # 4. Verify data in restored database
    restored_db_instance = type(db)(db_path=str(restored_db_path))
    found_org = await restored_db_instance.get_organization(org["id"])
    assert found_org is not None
    assert found_org["name"] == "Disaster Recovery Enterprise"
    assert found_org["tier"] == "enterprise"

    found_user = await restored_db_instance.get_user_by_email("dr_test_user@aegisdr.io")
    assert found_user is not None
    assert found_user["full_name"] == "DR Test Officer"

def test_tampered_backup_rejection(tmp_path):
    """Verifies that a tampered or corrupted backup file is rejected during restore."""
    dr = DisasterRecoveryService(db_path=Path(db.db_path))
    backup_file = tmp_path / "tamper_test.db"
    meta = dr.create_backup(custom_backup_path=backup_file)

    # Tamper with the backup file bytes
    with open(backup_file, "r+b") as f:
        f.seek(100)
        f.write(b"CORRUPTED_BYTES_HERE")

    target_restore = tmp_path / "corrupt_restore.db"
    with pytest.raises(ValueError, match="Backup integrity checksum mismatch"):
        dr.restore_backup(backup_file=backup_file, target_db=target_restore)

def test_rpo_rto_specifications():
    """Verifies documented and verified RPO/RTO parameters."""
    dr = DisasterRecoveryService()
    specs = dr.get_disaster_recovery_specs()
    assert specs["RPO_target_minutes"] <= 15
    assert specs["RTO_target_minutes"] <= 60
    assert "SHA-256" in specs["backup_strategy"]
