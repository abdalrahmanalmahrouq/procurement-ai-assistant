"""Saved report previews and exports."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

from app.services.report_service import REPORT_DIR, csv_export, get_report, list_reports


router = APIRouter(prefix="/api/reports", tags=["Reports"])


def report_or_404(report_id: str) -> dict:
    try:
        canonical_id = str(UUID(report_id))
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Report not found.") from error
    report = get_report(canonical_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


@router.get("")
def reports():
    return list_reports()


@router.get("/{report_id}")
def report_detail(report_id: str):
    return report_or_404(report_id)


@router.get("/{report_id}/pdf")
def report_pdf(report_id: str, download: bool = False):
    report = report_or_404(report_id)
    path = REPORT_DIR / f"{report['id']}.pdf"
    if not path.is_file():
        raise HTTPException(status_code=503, detail="The report PDF is unavailable.")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"procurement-report-{report['period'].replace(' ', '-')}.pdf",
        content_disposition_type="attachment" if download else "inline",
    )


@router.get("/{report_id}/csv/{section}")
def report_csv(report_id: str, section: str):
    report = report_or_404(report_id)
    if report["spec"]["export_format"] != "pdf_csv":
        raise HTTPException(status_code=404, detail="CSV export is not available for this report.")
    if section not in report["spec"]["sections"]:
        raise HTTPException(status_code=404, detail="Report section not found.")
    try:
        content = csv_export(report, section)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return Response(content=content, media_type="text/csv", headers={"Content-Disposition": f'attachment; filename="procurement-{section}-{report["period"].replace(" ", "-")}.csv"'})
