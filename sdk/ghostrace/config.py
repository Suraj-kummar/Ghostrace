"""
ghostrace.config
~~~~~~~~~~~~~~~~
Global configuration singleton. Set once via ghostrace.init() and read
everywhere else through get_config().
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
_INSTANCE: Optional['GhostraceConfig'] = None

@dataclass
class GhostraceConfig:
    api_key: str = ''
    project: str = 'default'
    base_url: str = 'https://api.ghostrace.dev'
    debug: bool = False
    local_only: bool = False
    max_buffer_size: int = 100

    def is_configured(self) -> bool:
        pass

def init(api_key: str='', project: str='default', base_url: str='https://api.ghostrace.dev', debug: bool=False, local_only: bool=False) -> GhostraceConfig:
    pass

def get_config() -> GhostraceConfig:
    pass