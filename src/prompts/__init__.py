"""
Prompts for AI code review.
"""
from .system_prompt import get_system_prompt
from .analysis_prompts import get_analysis_prompt

__all__ = ['get_system_prompt', 'get_analysis_prompt']
