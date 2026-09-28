from dataclasses import dataclass
from fastapi import Depends, Header, HTTPException

@dataclass(frozen=True)
class DemoUser:
    id: str
    name: str
    role: str
    organization_scope: tuple[str, ...]

USERS = {
    "admin": DemoUser("admin", "Aarav — ESG Admin", "administrator", ("MEIL",)),
    "coordinator": DemoUser("coordinator", "Diya — Entity Coordinator", "coordinator", ("MEIL-INFRA",)),
    "owner": DemoUser("owner", "Kabir — Project Owner", "data_owner", ("ATLAS",)),
    "reviewer": DemoUser("reviewer", "Meera — EHS Reviewer", "reviewer", ("MEIL",)),
    "approver": DemoUser("approver", "Rohan — Approver", "approver", ("MEIL",)),
    "assurance": DemoUser("assurance", "Sara — Assurance", "assurance", ("MEIL",)),
}

PERMISSIONS = {
    "administrator": {"*"},
    "coordinator": {"read", "assign", "collect", "review"},
    "data_owner": {"read", "collect", "submit"},
    "reviewer": {"read", "review", "request_changes"},
    "approver": {"read", "approve", "lock"},
    "assurance": {"read", "assure"},
}

def current_user(x_demo_user: str = Header(default="admin")) -> DemoUser:
    user = USERS.get(x_demo_user)
    if not user:
        raise HTTPException(status_code=401, detail="Unknown demo user")
    return user

def require(permission: str):
    def dependency(user: DemoUser = Depends(current_user)) -> DemoUser:
        allowed = PERMISSIONS[user.role]
        if "*" not in allowed and permission not in allowed:
            raise HTTPException(status_code=403, detail=f"Role {user.role} cannot {permission}")
        return user
    return dependency
