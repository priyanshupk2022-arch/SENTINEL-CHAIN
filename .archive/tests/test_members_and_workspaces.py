"""Test Suite for Workspaces, Team Memberships, and Invitations."""
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.database import db

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    db._init_db()

@pytest.mark.asyncio
async def test_workspace_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        t_now = int(asyncio.get_event_loop().time() * 1000)
        reg = await ac.post("/api/auth/register", json={
            "full_name": "Workspace Admin",
            "organization_name": "Cloud Infra Inc",
            "email": f"ws_admin_{t_now}@cloudinfra.io",
            "password": "Password123!"
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. List initial default workspace
        list_res = await ac.get("/api/workspaces", headers=headers)
        assert list_res.status_code == 200
        workspaces = list_res.json()
        assert len(workspaces) >= 1

        # 2. Create new staging workspace
        create_res = await ac.post("/api/workspaces", json={"name": "Staging Environment", "slug": "staging"}, headers=headers)
        assert create_res.status_code == 200
        new_ws_id = create_res.json()["id"]

        # 3. Verify created workspace appears in list
        list2 = await ac.get("/api/workspaces", headers=headers)
        assert any(w["id"] == new_ws_id for w in list2.json())

        # 4. Delete staging workspace
        del_res = await ac.delete(f"/api/workspaces/{new_ws_id}", headers=headers)
        assert del_res.status_code == 200

@pytest.mark.asyncio
async def test_team_members_and_invitations_lifecycle():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        t_now = int(asyncio.get_event_loop().time() * 1000)
        owner_reg = await ac.post("/api/auth/register", json={
            "full_name": "Team Owner",
            "organization_name": "DevSecOps Corp",
            "email": f"owner_{t_now}@devsecops.com",
            "password": "Password123!"
        })
        owner_token = owner_reg.json()["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}

        # 1. Invite a Security Lead
        invitee_email = f"sec_lead_{t_now}@devsecops.com"
        inv_res = await ac.post("/api/invitations", json={
            "email": invitee_email,
            "role": "security_lead"
        }, headers=owner_headers)
        assert inv_res.status_code == 200
        assert "token" in inv_res.json()

        # 2. List pending invitations
        inv_list = await ac.get("/api/invitations", headers=owner_headers)
        assert inv_list.status_code == 200
        assert any(i["email"] == invitee_email for i in inv_list.json())

        # 3. List organization members (owner is initial member)
        members_res = await ac.get("/api/members", headers=owner_headers)
        assert members_res.status_code == 200
        members = members_res.json()
        assert len(members) >= 1
        assert members[0]["role"] == "owner"
