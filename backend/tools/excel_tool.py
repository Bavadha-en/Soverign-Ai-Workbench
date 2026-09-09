import os
import time
from typing import Optional, Dict, Any, List
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from backend.models.schemas import CreateExcelOutput
from backend.services.audit_service import audit_service


def create_excel(
    output_path: str,
    data: List[Dict[str, Any]],
    sheet_name: str = "Sheet1",
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates an Excel (.xlsx) spreadsheet with styled headers and data using openpyxl.
    Logs action to audit_service.
    """
    start_time = time.time()
    try:
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = sheet_name

        rows_written = 0
        if data and len(data) > 0:
            headers = list(data[0].keys())

            # Header styling
            header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
            header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
            thin_border = Border(
                left=Side(style="thin", color="D9D9D9"),
                right=Side(style="thin", color="D9D9D9"),
                top=Side(style="thin", color="D9D9D9"),
                bottom=Side(style="thin", color="D9D9D9")
            )

            # Header row
            for col_idx, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_idx, value=str(header))
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = thin_border

            # Data rows
            for row_idx, row_data in enumerate(data, 2):
                for col_idx, header in enumerate(headers, 1):
                    val = row_data.get(header, "")
                    cell = ws.cell(row=row_idx, column=col_idx, value=val)
                    cell.border = thin_border
                    if isinstance(val, (int, float)):
                        cell.alignment = Alignment(horizontal="right", vertical="center")
                    else:
                        cell.alignment = Alignment(horizontal="left", vertical="center")
                rows_written += 1

            # Auto-fit column widths
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                col_letter = openpyxl.utils.get_column_letter(col[0].column)
                ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        wb.save(output_path)
        file_size = os.path.getsize(output_path)

        duration = round((time.time() - start_time) * 1000, 2)
        audit_service.log_action(
            action="CREATE_EXCEL",
            component="tools.excel_tool",
            status="SUCCESS",
            task_id=task_id,
            duration_ms=duration,
            details={"output_path": output_path, "file_size": file_size, "rows_written": rows_written}
        )

        return CreateExcelOutput(
            success=True,
            output_path=output_path,
            rows_written=rows_written,
            file_size=file_size,
            error=None
        ).model_dump()
    except Exception as e:
        duration = round((time.time() - start_time) * 1000, 2)
        audit_service.log_action(
            action="CREATE_EXCEL",
            component="tools.excel_tool",
            status="FAILURE",
            task_id=task_id,
            duration_ms=duration,
            details={"output_path": output_path, "error": str(e)}
        )
        return CreateExcelOutput(
            success=False,
            output_path=output_path,
            rows_written=0,
            file_size=0,
            error=str(e)
        ).model_dump()
