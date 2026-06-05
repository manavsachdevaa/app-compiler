import json
import re
from typing import Any


REPAIR_SYSTEM_PROMPT = """You are a JSON repair engine. Fix the broken JSON below and return ONLY valid JSON.

Rules:
- Fix syntax errors (missing commas, brackets, quotes)
- Do NOT change the data structure or values
- Return ONLY the repaired JSON, nothing else
- If a field value is clearly wrong type (e.g. string where array expected), fix it
"""

class ValidationResult:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.repairs: list[str] = []
        self.valid = True

    def add_error(self, msg: str):
        self.errors.append(msg)
        self.valid = False

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    def add_repair(self, msg: str):
        self.repairs.append(msg)


def repair_json(raw: str) -> dict:
    """Try to parse JSON."""
    raw = re.sub(r"^```json\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    return json.loads(raw)


def validate_db_schema(db: dict, result: ValidationResult) -> dict:
    """Validate and auto-repair DB schema."""
    if "tables" not in db:
        db["tables"] = []
        result.add_repair("Added missing 'tables' key to DB schema")

    required_system_fields = {"id", "created_at", "updated_at"}
    
    for table in db.get("tables", []):
        if "name" not in table:
            result.add_error("DB table missing 'name'")
            continue
        
        if "fields" not in table:
            table["fields"] = []
            result.add_repair(f"Added missing 'fields' to table {table['name']}")

        field_names = {f["name"] for f in table["fields"]}
        
        # Ensure system fields exist
        if "id" not in field_names:
            table["fields"].insert(0, {
                "name": "id", "type": "uuid", "primary_key": True,
                "required": True, "unique": True, "indexed": True
            })
            result.add_repair(f"Added missing 'id' field to table {table['name']}")
        
        if "created_at" not in field_names:
            table["fields"].append({
                "name": "created_at", "type": "datetime",
                "required": True, "default": "now()"
            })
            result.add_repair(f"Added missing 'created_at' to table {table['name']}")
        
        if "updated_at" not in field_names:
            table["fields"].append({
                "name": "updated_at", "type": "datetime",
                "required": True, "default": "now()"
            })
            result.add_repair(f"Added missing 'updated_at' to table {table['name']}")

        # Validate foreign keys
        for field in table["fields"]:
            if field.get("foreign_key"):
                fk = field["foreign_key"]
                if "." not in fk:
                    field["foreign_key"] = f"{fk}.id"
                    result.add_repair(f"Fixed malformed FK {fk} in {table['name']}")

    # Check for users table
    table_names = [t["name"] for t in db.get("tables", [])]
    if "users" not in table_names and "user" not in table_names:
        result.add_warning("No users table found in DB schema")

    return db


def validate_api_schema(api: dict, db: dict, result: ValidationResult) -> dict:
    """Validate API schema and cross-check with DB."""
    if "endpoints" not in api:
        api["endpoints"] = []
        result.add_repair("Added missing 'endpoints' key to API schema")

    if "base_path" not in api:
        api["base_path"] = "/api/v1"
        result.add_repair("Added default base_path to API schema")

    db_table_names = {t["name"] for t in db.get("tables", [])}
    db_table_fields: dict[str, set] = {}
    for t in db.get("tables", []):
        db_table_fields[t["name"]] = {f["name"] for f in t.get("fields", [])}

    # Check auth endpoints exist
    paths = [e["path"] for e in api.get("endpoints", [])]
    if not any("/auth/login" in p for p in paths):
        api["endpoints"].insert(0, {
            "method": "POST",
            "path": "/auth/login",
            "summary": "Authenticate user",
            "auth_required": False,
            "roles": [],
            "body_params": [
                {"name": "email", "type": "string", "required": True, "description": "User email"},
                {"name": "password", "type": "string", "required": True, "description": "User password"}
            ],
            "query_params": [],
            "path_params": [],
            "response_fields": ["token", "refresh_token", "user"],
            "db_table": "users"
        })
        result.add_repair("Added missing /auth/login endpoint")

    if not any("/auth/register" in p for p in paths):
        api["endpoints"].insert(1, {
            "method": "POST",
            "path": "/auth/register",
            "summary": "Register new user",
            "auth_required": False,
            "roles": [],
            "body_params": [
                {"name": "email", "type": "string", "required": True, "description": "User email"},
                {"name": "password", "type": "string", "required": True, "description": "Password"},
                {"name": "name", "type": "string", "required": True, "description": "Full name"}
            ],
            "query_params": [],
            "path_params": [],
            "response_fields": ["id", "email", "name", "role"],
            "db_table": "users"
        })
        result.add_repair("Added missing /auth/register endpoint")

    # Validate body params match DB fields
    for endpoint in api.get("endpoints", []):
        db_table = endpoint.get("db_table")
        if db_table and db_table in db_table_fields:
            valid_fields = db_table_fields[db_table]
            for param in endpoint.get("body_params", []):
                if param["name"] not in valid_fields and param["name"] not in {"password", "token", "refresh_token"}:
                    result.add_warning(
                        f"API param '{param['name']}' in {endpoint['path']} not found in DB table '{db_table}'"
                    )

    return api


def validate_ui_schema(ui: dict, api: dict, auth: dict, result: ValidationResult) -> dict:
    """Validate UI schema and cross-check with API + Auth."""
    if "pages" not in ui:
        ui["pages"] = []
        result.add_repair("Added missing 'pages' key to UI schema")

    api_paths = {e["path"] for e in api.get("endpoints", [])}
    auth_role_names = {r["name"] for r in auth.get("roles", [])}

    # Ensure login page exists
    routes = [p["route"] for p in ui.get("pages", [])]
    if "/login" not in routes:
        ui["pages"].insert(0, {
            "name": "Login",
            "route": "/login",
            "title": "Sign In",
            "auth_required": False,
            "roles": [],
            "layout": "centered",
            "components": [
                {
                    "id": "login_form",
                    "type": "form",
                    "title": "Sign In",
                    "fields": [
                        {"name": "email", "label": "Email", "component": "input",
                         "api_field": "email", "required": True, "placeholder": "you@example.com"},
                        {"name": "password", "label": "Password", "component": "input",
                         "api_field": "password", "required": True, "placeholder": "••••••••"}
                    ],
                    "api_endpoint": "/auth/login",
                    "roles": [],
                    "props": {"submit_label": "Sign In"}
                }
            ]
        })
        result.add_repair("Added missing /login page to UI schema")

    # Validate roles on pages
    for page in ui.get("pages", []):
        for role in page.get("roles", []):
            if role not in auth_role_names and role != "":
                result.add_warning(f"UI page '{page['name']}' references undefined role '{role}'")

        # Validate component api_endpoints
        for comp in page.get("components", []):
            endpoint = comp.get("api_endpoint")
            if endpoint:
                # Strip base path for comparison
                short_path = endpoint.replace("/api/v1", "")
                if endpoint not in api_paths and short_path not in api_paths:
                    result.add_warning(
                        f"UI component '{comp.get('id')}' references non-existent API endpoint '{endpoint}'"
                    )

    return ui


def validate_auth_schema(auth: dict, result: ValidationResult) -> dict:
    """Validate auth schema completeness."""
    if "roles" not in auth:
        auth["roles"] = []
        result.add_repair("Added missing 'roles' key to auth schema")

    if "strategy" not in auth:
        auth["strategy"] = "jwt"
        result.add_repair("Added default JWT strategy to auth")

    if "session_ttl_hours" not in auth:
        auth["session_ttl_hours"] = 24
        result.add_repair("Added default session TTL of 24 hours")

    # Ensure at least one default role
    has_default = any(r.get("is_default") for r in auth.get("roles", []))
    if not has_default and auth.get("roles"):
        # Set the last non-admin role as default
        for role in reversed(auth["roles"]):
            if role.get("name") != "admin":
                role["is_default"] = True
                result.add_repair(f"Set '{role['name']}' as default role")
                break

    # Ensure admin role exists
    role_names = [r["name"] for r in auth.get("roles", [])]
    if "admin" not in role_names:
        auth["roles"].insert(0, {
            "name": "admin",
            "description": "Full system administrator",
            "is_default": False,
            "permissions": [{"resource": "*", "actions": ["*"]}]
        })
        result.add_repair("Added missing admin role to auth schema")

    return auth


def validate_cross_layer(db: dict, api: dict, ui: dict, auth: dict, result: ValidationResult):
    """Final cross-layer consistency check."""
    
    # 1. Check all DB FK references point to real tables
    table_names = {t["name"] for t in db.get("tables", [])}
    for table in db.get("tables", []):
        for field in table.get("fields", []):
            fk = field.get("foreign_key")
            if fk and "." in fk:
                ref_table = fk.split(".")[0]
                if ref_table not in table_names:
                    result.add_error(
                        f"FK '{fk}' in table '{table['name']}' references non-existent table '{ref_table}'"
                    )

    # 2. Check API roles exist in auth
    auth_roles = {r["name"] for r in auth.get("roles", [])}
    for endpoint in api.get("endpoints", []):
        for role in endpoint.get("roles", []):
            if role not in auth_roles:
                result.add_warning(f"API endpoint {endpoint['path']} references undefined role '{role}'")

    # 3. Check UI form fields map to API params
    api_endpoint_params: dict[str, set] = {}
    for ep in api.get("endpoints", []):
        params = {p["name"] for p in ep.get("body_params", [])}
        api_endpoint_params[ep["path"]] = params
        api_endpoint_params[ep["path"].replace("/api/v1", "")] = params

    for page in ui.get("pages", []):
        for comp in page.get("components", []):
            endpoint = comp.get("api_endpoint", "")
            if endpoint and endpoint in api_endpoint_params:
                valid_params = api_endpoint_params[endpoint]
                for field in comp.get("fields", []):
                    api_field = field.get("api_field")
                    if api_field and api_field not in valid_params:
                        result.add_warning(
                            f"UI field '{field['name']}' maps to api_field '{api_field}' "
                            f"which is not in endpoint '{endpoint}'"
                        )


def run_validation(schemas: dict[str, Any]) -> tuple[dict[str, Any], ValidationResult]:
    """Run full validation pipeline on all schemas."""
    result = ValidationResult()
    
    db = schemas.get("database", {})
    api = schemas.get("api", {})
    ui = schemas.get("ui", {})
    auth = schemas.get("auth", {})
    
    # Validate and repair each layer
    db = validate_db_schema(db, result)
    api = validate_api_schema(api, db, result)
    auth = validate_auth_schema(auth, result)
    ui = validate_ui_schema(ui, api, auth, result)
    
    # Cross-layer check
    validate_cross_layer(db, api, ui, auth, result)
    
    return {
        "database": db,
        "api": api,
        "ui": ui,
        "auth": auth,
    }, result
