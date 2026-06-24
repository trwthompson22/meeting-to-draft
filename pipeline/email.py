"""
Email body formatting: render analysis output into an HTML email body.
"""


def render_body(summary: str, action_items: list[dict]) -> str:
    """
    Render an HTML email body from a meeting summary and action items.

    Args:
        summary:      Plain-text meeting summary.
        action_items: List of dicts with keys: description, owner, deadline.

    Returns:
        HTML string suitable for use as an Outlook message body.

    Raises:
        NotImplementedError: Placeholder — replace body with real impl.
    """
    raise NotImplementedError("email.render_body is not yet implemented")
