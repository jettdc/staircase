from dataclasses import dataclass, field
from typing import Tuple, List, Any, Callable


@dataclass
class SubstepRegistration:
    desc: str
    substep_name: str
    step_type: str = '_Substep'
    results: Tuple[bool, Any] = (None, None)


@dataclass
class StepRegistration:
    step_type: str
    step_index: int
    on_pass: str
    on_fail: str
    desc: str
    method_reference: Callable
    results: Tuple[bool, Any] = (None, None)
    substeps: List[SubstepRegistration] = field(default_factory=lambda: [])
