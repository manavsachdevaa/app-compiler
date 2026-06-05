from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Literal
from enum import Enum

# ─── Enums ────────────────────────────────────────────────────────────────────

class FieldType(str, Enum):
    string = "string"
    integer = "integer"
    float_ = "float"
    boolean = "boolean"
    datetime = "datetime"
    text = "text"
    uuid = "uuid"
    enum = "enum"
    json = "json"

class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"

class ComponentType(str, Enum):
    table = "table"
    form = "form"
    card = "card"
    chart = "chart"
    list_ = "list"
    modal = "modal"
    navbar = "navbar"
    sidebar = "sidebar"
    button = "button"
    input = "input"
    badge = "badge"
    stats = "stats"

# ─── Database Schema ──────────────────────────────────────────────────────────

class DBField(BaseModel):
    name: str
    type: FieldType
    required: bool = True
    unique: bool = False
    primary_key: bool = False
    foreign_key: Optional[str] = None  # "table.field"
    default: Optional[Any] = None
    enum_values: Optional[List[str]] = None
    indexed: bool = False

class DBTable(BaseModel):
    name: str
    fields: List[DBField]
    relations: List[str] = []  # e.g. ["user has_many contacts"]
    description: str = ""

class DBSchema(BaseModel):
    tables: List[DBTable]

    @field_validator("tables")
    @classmethod
    def at_least_one_table(cls, v):
        if not v:
            raise ValueError("DB schema must have at least one table")
        return v

# ─── API Schema ───────────────────────────────────────────────────────────────

class APIParam(BaseModel):
    name: str
    type: FieldType
    required: bool = True
    description: str = ""

class APIEndpoint(BaseModel):
    method: HttpMethod
    path: str
    summary: str
    auth_required: bool = True
    roles: List[str] = []
    body_params: List[APIParam] = []
    query_params: List[APIParam] = []
    path_params: List[APIParam] = []
    response_fields: List[str] = []
    db_table: Optional[str] = None  # which table this endpoint touches

class APISchema(BaseModel):
    base_path: str = "/api/v1"
    endpoints: List[APIEndpoint]

    @field_validator("endpoints")
    @classmethod
    def at_least_one_endpoint(cls, v):
        if not v:
            raise ValueError("API schema must have at least one endpoint")
        return v

# ─── UI Schema ────────────────────────────────────────────────────────────────

class UIField(BaseModel):
    name: str
    label: str
    component: str  # input, select, textarea, checkbox, etc.
    api_field: str  # maps to API param
    required: bool = True
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None  # for selects

class UIComponent(BaseModel):
    id: str
    type: ComponentType
    title: str
    fields: List[UIField] = []
    api_endpoint: Optional[str] = None  # maps to API path
    roles: List[str] = []  # which roles can see this
    props: Dict[str, Any] = {}

class UIPage(BaseModel):
    name: str
    route: str
    title: str
    auth_required: bool = True
    roles: List[str] = []
    components: List[UIComponent]
    layout: str = "default"

class UISchema(BaseModel):
    pages: List[UIPage]
    theme: str = "light"
    nav_items: List[str] = []

    @field_validator("pages")
    @classmethod
    def at_least_one_page(cls, v):
        if not v:
            raise ValueError("UI schema must have at least one page")
        return v

# ─── Auth Schema ──────────────────────────────────────────────────────────────

class AuthPermission(BaseModel):
    resource: str
    actions: List[str]  # create, read, update, delete, *

class AuthRole(BaseModel):
    name: str
    description: str
    permissions: List[AuthPermission]
    is_default: bool = False

class AuthSchema(BaseModel):
    strategy: str = "jwt"
    roles: List[AuthRole]
    session_ttl_hours: int = 24
    refresh_token: bool = True
    oauth_providers: List[str] = []

# ─── Business Logic ───────────────────────────────────────────────────────────

class BusinessRule(BaseModel):
    name: str
    type: str  # "premium_gate", "role_access", "validation", "workflow"
    description: str
    condition: str
    action: str
    affected_endpoints: List[str] = []
    affected_ui: List[str] = []

class BusinessLogic(BaseModel):
    rules: List[BusinessRule] = []
    payment_enabled: bool = False
    payment_provider: Optional[str] = None
    premium_features: List[str] = []

# ─── Top-Level App Config ─────────────────────────────────────────────────────

class AppMeta(BaseModel):
    name: str
    description: str
    version: str = "1.0.0"
    entities: List[str] = []
    features: List[str] = []
    assumptions: List[str] = []

class PipelineMeta(BaseModel):
    stage_latencies_ms: Dict[str, int] = {}
    total_latency_ms: int = 0
    retries: int = 0
    repairs: List[str] = []
    warnings: List[str] = []
    success: bool = True

class AppConfig(BaseModel):
    app: AppMeta
    database: DBSchema
    api: APISchema
    ui: UISchema
    auth: AuthSchema
    business_logic: BusinessLogic
    meta: PipelineMeta = Field(default_factory=PipelineMeta)
