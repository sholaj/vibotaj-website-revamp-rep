"""Email HTML templates for transactional notifications (PRD-020).

All emails share a base layout with per-org branding.
Templates are rendered as HTML strings — no external template engine needed.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class OrgBranding:
    """Per-organization branding for email templates."""

    org_name: str = "TraceHub"
    logo_url: Optional[str] = None
    primary_color: str = "#2563EB"  # Blue-600


# --- Base layout ---


def _base_layout(
    body_html: str,
    branding: OrgBranding,
    unsubscribe_url: Optional[str] = None,
) -> str:
    """Wrap body content in the standard email layout."""
    logo_section = ""
    if branding.logo_url:
        logo_section = (
            f'<img src="{branding.logo_url}" alt="{branding.org_name}" '
            f'style="max-height:40px;margin-bottom:16px;" />'
        )
    else:
        logo_section = (
            f'<div style="font-size:20px;font-weight:700;'
            f"color:{branding.primary_color};margin-bottom:16px;"
            f'">{branding.org_name}</div>'
        )

    unsub = ""
    if unsubscribe_url:
        unsub = (
            f'<p style="margin-top:8px;">'
            f'<a href="{unsubscribe_url}" style="color:#6B7280;font-size:12px;">'
            f"Manage notification preferences</a></p>"
        )

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;padding:0;background-color:#F9FAFB;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#F9FAFB;padding:32px 16px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background-color:#FFFFFF;border-radius:8px;border:1px solid #E5E7EB;overflow:hidden;">
<!-- Header -->
<tr><td style="padding:24px 32px;border-bottom:2px solid {branding.primary_color};">
{logo_section}
</td></tr>
<!-- Body -->
<tr><td style="padding:32px;">
{body_html}
</td></tr>
<!-- Footer -->
<tr><td style="padding:24px 32px;background-color:#F9FAFB;border-top:1px solid #E5E7EB;">
<p style="margin:0;font-size:12px;color:#6B7280;">
Sent by TraceHub on behalf of {branding.org_name}
</p>
{unsub}
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


# --- Template renderers ---


def render_document_uploaded(
    doc_type: str,
    doc_name: str,
    uploaded_by: str,
    shipment_ref: str,
    shipment_url: str,
    branding: OrgBranding = OrgBranding(),
) -> tuple[str, str]:
    """Render document uploaded email. Returns (subject, html)."""
    subject = f"[TraceHub] {doc_type} uploaded for {shipment_ref}"
    body = f"""
<h2 style="margin:0 0 16px;font-size:18px;color:#111827;">Document Uploaded</h2>
<p style="color:#374151;">A new document has been uploaded to shipment <strong>{shipment_ref}</strong>.</p>
<table style="width:100%;margin:16px 0;border-collapse:collapse;">
<tr><td style="padding:8px 0;color:#6B7280;">Document Type</td><td style="padding:8px 0;font-weight:600;">{doc_type}</td></tr>
<tr><td style="padding:8px 0;color:#6B7280;">File Name</td><td style="padding:8px 0;">{doc_name}</td></tr>
<tr><td style="padding:8px 0;color:#6B7280;">Uploaded By</td><td style="padding:8px 0;">{uploaded_by}</td></tr>
</table>
<a href="{shipment_url}" style="display:inline-block;padding:10px 24px;background-color:{branding.primary_color};color:#FFFFFF;text-decoration:none;border-radius:6px;font-weight:600;">View Shipment</a>
"""
    return subject, _base_layout(body, branding)


def render_document_approved(
    doc_type: str,
    shipment_ref: str,
    approved_by: str,
    shipment_url: str,
    notes: Optional[str] = None,
    branding: OrgBranding = OrgBranding(),
) -> tuple[str, str]:
    """Render document approved email."""
    subject = f"[TraceHub] {doc_type} approved for {shipment_ref}"
    notes_html = (
        f'<p style="color:#374151;margin-top:12px;"><em>Notes: {notes}</em></p>'
        if notes
        else ""
    )
    body = f"""
<h2 style="margin:0 0 16px;font-size:18px;color:#059669;">Document Approved</h2>
<p style="color:#374151;">The <strong>{doc_type}</strong> for shipment <strong>{shipment_ref}</strong> has been approved by {approved_by}.</p>
{notes_html}
<a href="{shipment_url}" style="display:inline-block;margin-top:16px;padding:10px 24px;background-color:{branding.primary_color};color:#FFFFFF;text-decoration:none;border-radius:6px;font-weight:600;">View Shipment</a>
"""
    return subject, _base_layout(body, branding)


def render_document_rejected(
    doc_type: str,
    shipment_ref: str,
    rejected_by: str,
    reason: str,
    shipment_url: str,
    branding: OrgBranding = OrgBranding(),
) -> tuple[str, str]:
    """Render document rejected email."""
    subject = f"[TraceHub] {doc_type} rejected for {shipment_ref}"
    body = f"""
<h2 style="margin:0 0 16px;font-size:18px;color:#DC2626;">Document Rejected</h2>
<p style="color:#374151;">The <strong>{doc_type}</strong> for shipment <strong>{shipment_ref}</strong> has been rejected by {rejected_by}.</p>
<div style="margin:16px 0;padding:12px 16px;background-color:#FEF2F2;border-left:4px solid #DC2626;border-radius:4px;">
<p style="margin:0;color:#991B1B;font-weight:600;">Reason:</p>
<p style="margin:4px 0 0;color:#991B1B;">{reason}</p>
</div>
<a href="{shipment_url}" style="display:inline-block;margin-top:16px;padding:10px 24px;background-color:{branding.primary_color};color:#FFFFFF;text-decoration:none;border-radius:6px;font-weight:600;">View Shipment</a>
"""
    return subject, _base_layout(body, branding)


def render_shipment_status_change(
    shipment_ref: str,
    old_status: str,
    new_status: str,
    shipment_url: str,
    branding: OrgBranding = OrgBranding(),
) -> tuple[str, str]:
    """Render shipment status change email."""
    subject = f"[TraceHub] Shipment {shipment_ref} status: {new_status}"
    body = f"""
<h2 style="margin:0 0 16px;font-size:18px;color:#111827;">Shipment Status Update</h2>
<p style="color:#374151;">Shipment <strong>{shipment_ref}</strong> status has changed.</p>
<table style="width:100%;margin:16px 0;border-collapse:collapse;">
<tr><td style="padding:8px 0;color:#6B7280;">Previous Status</td><td style="padding:8px 0;">{old_status}</td></tr>
<tr><td style="padding:8px 0;color:#6B7280;">New Status</td><td style="padding:8px 0;font-weight:600;color:{branding.primary_color};">{new_status}</td></tr>
</table>
<a href="{shipment_url}" style="display:inline-block;padding:10px 24px;background-color:{branding.primary_color};color:#FFFFFF;text-decoration:none;border-radius:6px;font-weight:600;">View Shipment</a>
"""
    return subject, _base_layout(body, branding)


def render_compliance_alert(
    shipment_ref: str,
    alert_type: str,
    severity: str,
    message: str,
    shipment_url: str,
    branding: OrgBranding = OrgBranding(),
) -> tuple[str, str]:
    """Render compliance alert email."""
    subject = f"[TraceHub] Compliance alert: {shipment_ref}"
    severity_color = "#DC2626" if severity == "error" else "#D97706"
    body = f"""
<h2 style="margin:0 0 16px;font-size:18px;color:{severity_color};">Compliance Alert</h2>
<p style="color:#374151;">A compliance issue has been flagged for shipment <strong>{shipment_ref}</strong>.</p>
<div style="margin:16px 0;padding:12px 16px;background-color:#FEF3C7;border-left:4px solid {severity_color};border-radius:4px;">
<p style="margin:0;font-weight:600;color:#92400E;">{alert_type}</p>
<p style="margin:4px 0 0;color:#92400E;">{message}</p>
</div>
<a href="{shipment_url}" style="display:inline-block;margin-top:16px;padding:10px 24px;background-color:{branding.primary_color};color:#FFFFFF;text-decoration:none;border-radius:6px;font-weight:600;">View Shipment</a>
"""
    return subject, _base_layout(body, branding)


def render_invitation_sent(
    org_name: str,
    inviter_name: str,
    role: str,
    accept_url: str,
    branding: OrgBranding = OrgBranding(),
) -> tuple[str, str]:
    """Render invitation email."""
    subject = f"You've been invited to {org_name} on TraceHub"
    body = f"""
<h2 style="margin:0 0 16px;font-size:18px;color:#111827;">You're Invited</h2>
<p style="color:#374151;"><strong>{inviter_name}</strong> has invited you to join <strong>{org_name}</strong> as <strong>{role}</strong> on TraceHub.</p>
<p style="color:#374151;">TraceHub is a container tracking and compliance platform for international trade.</p>
<a href="{accept_url}" style="display:inline-block;margin-top:16px;padding:12px 32px;background-color:{branding.primary_color};color:#FFFFFF;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;">Accept Invitation</a>
<p style="color:#6B7280;font-size:12px;margin-top:16px;">If you did not expect this invitation, you can ignore this email.</p>
"""
    return subject, _base_layout(body, branding)


def render_invitation_accepted(
    org_name: str,
    accepted_by: str,
    role: str,
    branding: OrgBranding = OrgBranding(),
) -> tuple[str, str]:
    """Render invitation accepted notification to admin."""
    subject = f"[TraceHub] {accepted_by} joined {org_name}"
    body = f"""
<h2 style="margin:0 0 16px;font-size:18px;color:#059669;">New Team Member</h2>
<p style="color:#374151;"><strong>{accepted_by}</strong> has accepted the invitation and joined <strong>{org_name}</strong> as <strong>{role}</strong>.</p>
"""
    return subject, _base_layout(body, branding)


def render_expiry_warning(
    doc_type: str,
    shipment_ref: str,
    expiry_date: str,
    days_remaining: int,
    shipment_url: str,
    branding: OrgBranding = OrgBranding(),
) -> tuple[str, str]:
    """Render document expiry warning email."""
    urgency = "URGENT: " if days_remaining <= 3 else ""
    subject = f"[TraceHub] {urgency}{doc_type} expiring in {days_remaining} days"
    color = "#DC2626" if days_remaining <= 3 else "#D97706"
    body = f"""
<h2 style="margin:0 0 16px;font-size:18px;color:{color};">Document Expiring Soon</h2>
<p style="color:#374151;">The <strong>{doc_type}</strong> for shipment <strong>{shipment_ref}</strong> is expiring soon.</p>
<table style="width:100%;margin:16px 0;border-collapse:collapse;">
<tr><td style="padding:8px 0;color:#6B7280;">Expiry Date</td><td style="padding:8px 0;font-weight:600;color:{color};">{expiry_date}</td></tr>
<tr><td style="padding:8px 0;color:#6B7280;">Days Remaining</td><td style="padding:8px 0;font-weight:600;color:{color};">{days_remaining}</td></tr>
</table>
<a href="{shipment_url}" style="display:inline-block;margin-top:16px;padding:10px 24px;background-color:{branding.primary_color};color:#FFFFFF;text-decoration:none;border-radius:6px;font-weight:600;">View Shipment</a>
"""
    return subject, _base_layout(body, branding)
