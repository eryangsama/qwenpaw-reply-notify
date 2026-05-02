# -*- coding: utf-8 -*-
"""NotifyDoneHook: triggers avatar popup + sound when agent reply is done."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Defer import to avoid top-level import issues
_notify_done = None


def _get_notify_done():
    global _notify_done
    if _notify_done is None:
        try:
            import sys
            # Prefer A: workspace scripts, fallback to workspace default scripts
            _script_dir = Path(__file__).parent.parent / "scripts"
            if _script_dir.exists():
                sys.path.insert(0, str(_script_dir))
            from notify_done import notify_done
            _notify_done = notify_done
        except Exception as e:
            logger.error("Failed to import notify_done: %s", e)
            _notify_done = lambda: None
    return _notify_done


class NotifyDoneHook:
    """Hook that shows a small avatar popup when the agent finishes replying.

    Registered as a "post_reply" hook, so it fires after the agent has
    generated its response and before that response is sent to the user.
    """

    async def __call__(
        self,
        agent,  # noqa: ARG002
        kwargs: dict[str, Any],
        output: Any,
    ) -> dict[str, Any] | None:
        """Trigger the notification.

        Only fires when the agent's reply is final (no pending tool calls).
        This avoids duplicate notifications during multi-step reasoning.
        """
        try:
            # Only notify on final replies — skip intermediate steps with pending tool calls
            has_pending = self._has_pending_tools(agent, kwargs, output)
            if has_pending:
                return None

            notify_fn = _get_notify_done()
            notify_fn()
        except Exception as e:
            logger.debug("NotifyDoneHook error: %s", e)
        return None

    def _has_pending_tools(
        self,
        agent: Any,
        kwargs: dict[str, Any],
        output: Any,
    ) -> bool:
        """Return True if there are tool calls still pending in this step."""
        try:
            # Check output for tool calls that haven't executed yet
            if output is not None:
                # In ReActAgent, a response with tool_calls means tools are pending
                if hasattr(output, "tool_calls") and output.tool_calls:
                    return True
                if isinstance(output, dict):
                    tc = output.get("tool_calls")
                    if tc:
                        return True
        except Exception:
            pass
        return False
