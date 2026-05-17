from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    type: str
    content: str
    command: Optional[str] = None
    session_id: Optional[str] = None


class SessionList(BaseModel):
    id: str
    objective: str
    status: str
    timestamp: str


class TargetSummary(BaseModel):
    ip: str
    hostname: str
    os: str
    port_count: int
    cred_count: int
    vuln_count: int


class Credential(BaseModel):
    ip: str
    service: str
    username: str
    password: str


class Vulnerability(BaseModel):
    ip: str
    cve: str
    severity: str
    description: str
    port: int


class GraphNode(BaseModel):
    id: str
    label: str
    ip: str
    os: str
    ports: list
    is_gateway: bool


class GraphEdge(BaseModel):
    from_node: str
    to_node: str
    label: str
    service: str


class GraphResponse(BaseModel):
    nodes: list
    edges: list
