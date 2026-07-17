"""Dependency accessors: routers pull adapters off app.state and never learn
which implementation they got (§E)."""

from fastapi import Request

from app.config import Settings
from app.store import Store

def get_store(request: Request) -> Store:
    return request.app.state.store

def get_grader(request: Request):
    return request.app.state.grader

def get_brief_writer(request: Request):
    return request.app.state.brief_writer

def get_settings(request: Request) -> Settings:
    return request.app.state.settings
