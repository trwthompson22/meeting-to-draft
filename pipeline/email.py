"""
Email body formatting: render analysis output into an HTML email body.
"""


def render_body(summary: str, key_takeaways: list[str], action_items: list[dict]) -> str:
    """
    Render an HTML email body from a meeting summary, key takeaways, and action items.

    Args:
        summary:       1-2 sentence meeting summary.
        key_takeaways: List of key takeaway strings.
        action_items:  List of dicts with keys: description, owner, deadline.

    Returns:
        HTML string suitable for use as an Outlook message body.
    """
    takeaway_items = "".join(
        f"<li style='margin-bottom:4px;'>{item}</li>"
        for item in (key_takeaways or [])
    )
    takeaways_section = f"""
<h3 style='font-family:Arial,sans-serif;color:#333;margin-bottom:6px;'>Key Takeaways</h3>
<ul style='font-family:Arial,sans-serif;font-size:14px;color:#333;margin-top:0;padding-left:20px;'>
  {takeaway_items}
</ul>""" if takeaway_items else ""

    rows = ""
    for item in (action_items or []):
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
<h3 style='font-family:Arial,sans-serif;color:#333;margin-bottom:6px;'>Action Items</h3>
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
<h3 style='color:#333;margin-bottom:6px;'>Meeting Summary</h3>
<p style='margin-top:0;'>{summary}</p>
{takeaways_section}
{action_table}
</body></html>"""
