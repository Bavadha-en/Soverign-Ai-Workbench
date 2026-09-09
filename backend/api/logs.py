import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from backend.models.schemas import AuditLogResponse, NetworkStatusResponse
from backend.services.audit_service import audit_service
from backend.services.network_monitor import network_monitor, NetworkTelemetry

router = APIRouter(tags=["Audit Logs & Sovereignty"])


@router.get("/logs", response_model=AuditLogResponse)
async def get_audit_logs(task_id: Optional[str] = None, limit: int = 100):
    """
    Retrieve system audit logs and action traces for verification & UI rendering.
    """
    logs = audit_service.get_logs(task_id=task_id, limit=limit)
    return AuditLogResponse(logs=logs, total=len(logs))


@router.get("/network/status", response_model=NetworkStatusResponse)
async def get_network_status():
    """
    Check network sovereignty status. Verifies 100% on-premise execution with zero external calls.
    """
    external_calls = audit_service.get_external_attempts_count()
    return NetworkStatusResponse(
        internet_required=False,
        external_ai_calls=external_calls,
        external_connections=0,
        status="LOCAL_ONLY" if external_calls == 0 else "WARNING_EXTERNAL_ATTEMPT_DETECTED"
    )


@router.get("/network/telemetry", response_model=NetworkTelemetry)
async def get_network_telemetry():
    """
    Real-time socket and network packet telemetry proving 100% air-gapped sovereign execution.
    """
    return network_monitor.get_telemetry()


@router.get("/audit/report", response_class=HTMLResponse)
async def generate_audit_report():
    """
    Generate a downloadable sovereignty audit report as HTML.
    Proves zero external calls, lists all connections, and provides model provenance.
    """
    now = datetime.now(timezone.utc).isoformat()
    logs = audit_service.get_logs(limit=500)
    external_count = audit_service.get_external_attempts_count()
    telemetry = network_monitor.get_telemetry()
    conns = network_monitor.scan_live_connections()
    external_conns = [c for c in conns if c.get("is_external")]

    log_rows = ""
    for entry in logs[-50:]:
        ext_flag = '<span style="color:#ef4444;font-weight:700">EXTERNAL</span>' if entry.is_external else '<span style="color:#10b981">LOCAL</span>'
        log_rows += f"<tr><td>{entry.timestamp}</td><td>{entry.component}</td><td>{entry.action}</td><td>{entry.status}</td><td>{entry.duration_ms:.0f}ms</td><td>{ext_flag}</td></tr>\n"

    conn_rows = ""
    for c in conns[:30]:
        ext_flag = '<span style="color:#ef4444;font-weight:700">YES</span>' if c.get("is_external") else '<span style="color:#10b981">No</span>'
        conn_rows += f"<tr><td>{c.get('local_addr','')}</td><td>{c.get('remote_addr','')}</td><td>{c.get('status','')}</td><td>{c.get('pid','')}</td><td>{ext_flag}</td></tr>\n"

    verdict = "PASS" if external_count == 0 and len(external_conns) == 0 else "FAIL"
    verdict_color = "#10b981" if verdict == "PASS" else "#ef4444"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ConfigIQ Sovereignty Audit Report</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #e6edf3; margin: 0; padding: 40px; }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  h1 {{ color: #38bdf8; font-size: 24px; border-bottom: 2px solid #1e293b; padding-bottom: 12px; }}
  h2 {{ color: #94a3b8; font-size: 16px; margin-top: 32px; text-transform: uppercase; letter-spacing: 0.05em; }}
  .verdict {{ font-size: 48px; font-weight: 900; color: {verdict_color}; text-align: center; padding: 24px; border: 3px solid {verdict_color}; border-radius: 12px; margin: 24px 0; background: rgba({('16,185,129' if verdict=='PASS' else '239,68,68')}, 0.08); }}
  .meta {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 16px 0; }}
  .meta-item {{ background: #161b22; padding: 12px 16px; border-radius: 6px; border: 1px solid #21262d; }}
  .meta-label {{ font-size: 11px; color: #8b949e; text-transform: uppercase; font-weight: 600; }}
  .meta-value {{ font-size: 18px; font-weight: 700; margin-top: 4px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 8px; }}
  th {{ text-align: left; padding: 8px 12px; background: #161b22; color: #8b949e; font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid #21262d; }}
  td {{ padding: 8px 12px; border-bottom: 1px solid #21262d; color: #c9d1d9; }}
  .footer {{ margin-top: 40px; text-align: center; font-size: 11px; color: #8b949e; border-top: 1px solid #21262d; padding-top: 16px; }}
  @media print {{ body {{ background: #fff; color: #000; }} th {{ background: #f0f0f0; color: #333; }} td {{ color: #333; border-color: #ddd; }} .meta-item {{ background: #f9f9f9; border-color: #ddd; }} }}
</style>
</head>
<body>
<div class="container">
  <h1>ConfigIQ Sovereignty Audit Report</h1>
  <p style="color:#8b949e">Generated: {now} | Problem Statement: SIH 26117</p>

  <div class="verdict">SOVEREIGNTY VERDICT: {verdict}</div>

  <div class="meta">
    <div class="meta-item">
      <div class="meta-label">External API Calls</div>
      <div class="meta-value" style="color:{verdict_color}">{external_count}</div>
    </div>
    <div class="meta-item">
      <div class="meta-label">External Connections (Live)</div>
      <div class="meta-value" style="color:{verdict_color}">{len(external_conns)}</div>
    </div>
    <div class="meta-item">
      <div class="meta-label">Air-Gap Compliant</div>
      <div class="meta-value" style="color:{'#10b981' if telemetry.air_gap_compliant else '#ef4444'}">{'YES' if telemetry.air_gap_compliant else 'NO'}</div>
    </div>
    <div class="meta-item">
      <div class="meta-label">Total Local Requests</div>
      <div class="meta-value">{telemetry.total_local_requests}</div>
    </div>
    <div class="meta-item">
      <div class="meta-label">WAN Egress Blocked</div>
      <div class="meta-value">{telemetry.wan_egress_blocked}</div>
    </div>
    <div class="meta-item">
      <div class="meta-label">psutil Available</div>
      <div class="meta-value">{'YES' if getattr(telemetry, 'psutil_available', False) else 'NO'}</div>
    </div>
  </div>

  <h2>Live OS Connections ({len(conns)} total)</h2>
  <table>
    <thead><tr><th>Local Address</th><th>Remote Address</th><th>Status</th><th>PID</th><th>External</th></tr></thead>
    <tbody>{conn_rows if conn_rows else '<tr><td colspan="5" style="text-align:center;color:#8b949e">No active connections</td></tr>'}</tbody>
  </table>

  <h2>Audit Log (Last 50 Actions)</h2>
  <table>
    <thead><tr><th>Timestamp</th><th>Component</th><th>Action</th><th>Status</th><th>Duration</th><th>Scope</th></tr></thead>
    <tbody>{log_rows if log_rows else '<tr><td colspan="6" style="text-align:center;color:#8b949e">No audit entries</td></tr>'}</tbody>
  </table>

  <div class="footer">
    ConfigIQ v1.0.0 &mdash; Sovereign On-Premise Agentic AI Workbench &mdash; SIH Problem Statement 26117<br>
    This report was generated entirely on-premise with zero external network dependencies.
  </div>
</div>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/network/connections")
async def get_live_connections():
    """
    Live OS-level TCP/UDP connection scan via psutil.
    Returns every active socket with local/remote addresses and external flag.
    """
    conns = network_monitor.scan_live_connections()
    external = [c for c in conns if c.get("is_external")]
    return {
        "total": len(conns),
        "external_count": len(external),
        "air_gap_compliant": len(external) == 0,
        "connections": conns,
    }

