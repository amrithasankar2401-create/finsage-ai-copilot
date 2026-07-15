from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import uuid
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

from routers.cross_domain import get_vendor_risk_profile, get_bu_summary

router = APIRouter(prefix="/api/reports", tags=["Reports"])

REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../generated_reports'))

async def generate_risk_report_action(scope: str, id: str) -> str:
    """
    Generates a PDF risk report for either a vendor or a business unit.
    Returns the download URL.
    """
    if scope not in ["vendor", "business_unit"]:
        raise ValueError("scope must be 'vendor' or 'business_unit'")
        
    filename = f"report_{scope}_{id}_{uuid.uuid4().hex[:6]}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Heading1'], alignment=TA_CENTER, spaceAfter=20
    )
    h2_style = styles['Heading2']
    normal_style = styles['Normal']
    
    story = []
    
    # Title & Timestamp
    story.append(Paragraph(f"FinSage Formal Risk Report: {scope.replace('_', ' ').title()} {id}", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    story.append(Spacer(1, 20))
    
    if scope == "vendor":
        try:
            profile = await get_vendor_risk_profile(id)
            vendor_name = profile['vendor_info']['vendor_name']
            
            story.append(Paragraph(f"Vendor Name: {vendor_name}", h2_style))
            story.append(Paragraph(f"Category: {profile['vendor_info']['category']}", normal_style))
            story.append(Paragraph(f"Base Risk Rating: {profile['vendor_info']['risk_rating']}", normal_style))
            story.append(Spacer(1, 10))
            
            # AP Risk
            story.append(Paragraph("AP / Invoice Risk", h2_style))
            invoices = profile['high_risk_invoices']
            story.append(Paragraph(f"Total High-Risk Invoices: {len(invoices)}", normal_style))
            for inv in invoices:
                story.append(Paragraph(f"- {inv['invoice_id']} | Amount: ${inv['invoice_amount']} | Reason: {inv['risk_reason']}", normal_style))
            story.append(Spacer(1, 10))
            
            # Audit Risk
            story.append(Paragraph("Audit / GL Exceptions", h2_style))
            gl = profile['related_gl_exceptions']
            story.append(Paragraph(f"Exceptions in Vendor's Business Unit: {len(gl)}", normal_style))
            for exc in gl:
                story.append(Paragraph(f"- {exc['entry_id']} | Amount: ${exc['amount']} | Reason: {exc['exception_reason']}", normal_style))
            story.append(Spacer(1, 10))
            
            # Treasury Risk
            story.append(Paragraph("Treasury Cashflow Variance", h2_style))
            tr = profile['related_treasury_variance']
            story.append(Paragraph(f"Significant variance weeks for Vendor's Entity: {len(tr)}", normal_style))
            for v in tr:
                story.append(Paragraph(f"- Week: {v['week_start_date']} | Variance Amount: ${v['variance_amount']}", normal_style))
            
        except Exception as e:
            story.append(Paragraph(f"Error fetching vendor data: {str(e)}", normal_style))
            
    elif scope == "business_unit":
        try:
            summary = await get_bu_summary(id)
            story.append(Paragraph(f"Business Unit Risk Overview", h2_style))
            story.append(Paragraph(f"Total High Risk AP Exposure: ${summary['total_high_risk_invoice_amount']}", normal_style))
            story.append(Paragraph(f"Total Audit Exceptions: {summary['audit_exceptions_count']}", normal_style))
            story.append(Paragraph(f"Treasury Variance Incidents: {summary['treasury_variance_incidents']}", normal_style))
        except Exception as e:
            story.append(Paragraph(f"Error fetching BU data: {str(e)}", normal_style))
            
    doc.build(story)
    
    return f"/api/reports/download/{filename}"

@router.get("/download/{filename}")
async def download_report(filename: str):
    filepath = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath, media_type='application/pdf', filename=filename)
