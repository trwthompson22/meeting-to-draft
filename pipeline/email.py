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
    rows = ""
    for item in action_items:
        owner = item.get("owner") or "—"
        deadline = item.get("deadline") or "—"
        description = item.get("description", "")
        rows += (
            f"<tr>"
            f"<td style='padding:6px 12px;border:1px solid #ddd;'>{description}</td>"
            f"<td style='padding:6px 12px;border:1px solid #ddd;'>{owner}</td>"
            f"<td style='padding:6px 12px;border:1px solid #ddd;'>{deadline}</td>"
            f"</tr>"
        )

    action_table = ""
    if rows:
        action_table = f"""
<h3 style='font-family:Arial,sans-serif;color:#333;'>Action Items</h3>
<table style='border-collapse:collapse;font-family:Arial,sans-serif;font-size:14px;'>
  <thead>
    <tr style='background:#f5f5f5;'>
      <th style='padding:6px 12px;border:1px solid #ddd;text-align:left;'>Task</th>
      <th style='padding:6px 12px;border:1px solid #ddd;text-align:left;'>Owner</th>
      <th style='padding:6px 12px;border:1px solid #ddd;text-align:left;'>Deadline</th>
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>"""

    return f"""<html><body style='font-family:Arial,sans-serif;color:#333;font-size:14px;'>
<h3 style='color:#333;'>Meeting Summary</h3>
<p>{summary}</p>
{action_table}
</body></html>"""
