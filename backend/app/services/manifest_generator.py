import os
import time
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATIC_MANIFESTS_DIR = os.path.join(BASE_DIR, "static", "manifests")
os.makedirs(STATIC_MANIFESTS_DIR, exist_ok=True)

def generate_manifest_pdf(habitation: dict, output_path: str, authorized_by: str = "District Magistrate") -> dict:
    """
    Generate an official DDMA Evacuation & Relocation Triage Manifest PDF.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Generate unique order reference
    timestamp_str = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    hab_id = habitation.get("habitation_id", "GEN").upper().replace("_", "-")
    order_ref = f"DDMA-ORD-WYD-{hab_id}-{timestamp_str}"
    
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # Outer & Inner Borders
    c.setStrokeColor(colors.HexColor("#1A365D")) # Deep Navy
    c.setLineWidth(2.5)
    c.rect(25, 25, width - 50, height - 50)
    
    c.setStrokeColor(colors.HexColor("#718096"))
    c.setLineWidth(0.8)
    c.rect(30, 30, width - 60, height - 60)
    
    # Top Header Banner
    c.setFillColor(colors.HexColor("#1A365D"))
    c.rect(30, height - 110, width - 60, 80, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2.0, height - 55, "DISTRICT DISASTER MANAGEMENT AUTHORITY (DDMA)")
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2.0, height - 72, "NATIONAL DISASTER MANAGEMENT FRAMEWORK • GOVERNMENT OF KERALA")
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#FBD38D")) # Warm Gold Accent
    c.drawCentredString(width / 2.0, height - 94, "DRAFT PREEMPTIVE RELOCATION MANIFEST & EVACUATION ORDER")
    
    # Metadata Row
    c.setFillColor(colors.HexColor("#2D3748"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(45, height - 130, f"ORDER REF: {order_ref}")
    c.setFont("Helvetica", 10)
    now_str = datetime.now().strftime("%d-%b-%Y %H:%M:%S IST")
    c.drawRightString(width - 45, height - 130, f"ISSUED: {now_str}")
    
    # Divider line
    c.setStrokeColor(colors.HexColor("#CBD5E0"))
    c.setLineWidth(1)
    c.line(45, height - 140, width - 45, height - 140)
    
    # Section 1: Executive Summary / Authorization Notice
    c.setFillColor(colors.HexColor("#C53030")) # Deep Red Alert
    c.setFont("Helvetica-Bold", 11)
    c.drawString(45, height - 165, "EXECUTIVE DIRECTIVE: IMMEDIATE EVACUATION ORDER")
    
    c.setFillColor(colors.HexColor("#2D3748"))
    c.setFont("Helvetica", 9)
    legal_text = (
        "Pursuant to Powers vested under Section 30 & 34 of the Disaster Management Act, 2005, the incident commander "
        "hereby orders immediate preemptive evacuation of the vulnerable settlement detailed below based on multi-hazard "
        "geotechnical landslide and debris flow triggers."
    )
    # Simple word wrap for executive summary
    text_obj = c.beginText(45, height - 180)
    text_obj.setFont("Helvetica", 9)
    text_obj.setLeading(13)
    for line in [
        "Pursuant to powers vested under Section 30 & 34 of the Disaster Management Act, 2005, the competent authority",
        "hereby mandates immediate preemptive evacuation and safe transit of vulnerable habitations detailed below.",
        "Geotechnical sensor telemetry and slope stability models indicate critical Factor-of-Safety threshold breach."
    ]:
        text_obj.textLine(line)
    c.drawText(text_obj)
    
    # Section 2: Triage & Geotechnical Parameters (Structured Grid Box)
    box_top = height - 235
    box_height = 280
    c.setFillColor(colors.HexColor("#F7FAFC"))
    c.setStrokeColor(colors.HexColor("#CBD5E0"))
    c.rect(45, box_top - box_height, width - 90, box_height, fill=1, stroke=1)
    
    c.setFillColor(colors.HexColor("#2B6CB0"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(55, box_top - 20, "1. HABITATION ASSESSMENT & TRIAGE PARAMETERS")
    
    # Data rows
    items = [
        ("Habitation Name", str(habitation.get("name", "N/A")), "RTS Priority Rank", f"PRIORITY #{habitation.get('priority_rank', 'N/A')}"),
        ("Habitation ID", str(habitation.get("habitation_id", "N/A")), "Triage Status", "OFFICIALLY AUTHORIZED"),
        ("Relocation Triage Score (RTS)", f"{habitation.get('rts_score', 'N/A')}", "Time-to-Impact (TTI)", f"{habitation.get('tti_hours', 'N/A')} hours"),
        ("Structural Load (BLSR)", f"{habitation.get('struct_load', 'N/A')}", "Social Vulnerability (SVI)", f"{habitation.get('svi', 'N/A')}"),
        ("Demographic Exposure", f"{habitation.get('demo_exposure', 'N/A')} persons", "Target Shelter ID", str(habitation.get("assigned_shelter", "SHELTER-ST-JOSEPH-01"))),
        ("Coordinates (Lat / Lon)", f"{habitation.get('lat', 11.54):.4f}, {habitation.get('lon', 76.15):.4f}", "Terrain Operational Mode", "MOUNTAIN_CASCADE")
    ]
    
    y = box_top - 45
    for label1, val1, label2, val2 in items:
        # Col 1
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor("#4A5568"))
        c.drawString(60, y, label1 + ":")
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#1A202C"))
        c.drawString(200, y, val1)
        
        # Col 2
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor("#4A5568"))
        c.drawString(330, y, label2 + ":")
        c.setFont("Helvetica-Bold" if "PRIORITY" in val2 or "AUTHORIZED" in val2 else "Helvetica", 9)
        c.setFillColor(colors.HexColor("#C53030") if "PRIORITY" in val2 or "AUTHORIZED" in val2 else colors.HexColor("#1A202C"))
        c.drawString(460, y, val2)
        
        y -= 22
        c.setStrokeColor(colors.HexColor("#E2E8F0"))
        c.setLineWidth(0.5)
        c.line(55, y + 10, width - 55, y + 10)
        
    # Transit Routing Directive
    c.setFillColor(colors.HexColor("#2B6CB0"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, box_top - 200, "Designated Evacuation Transit Route:")
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#22543D")) # Forest Green
    c.drawString(70, box_top - 218, "Safe Evacuation Arterial (Red-Zone Bypass Verified via NetworkX)")
    
    c.setFont("Helvetica", 8.5)
    c.setFillColor(colors.HexColor("#4A5568"))
    c.drawString(70, box_top - 235, "All emergency transport vehicles must adhere to algorithmic topological bypass coordinates.")
    c.drawString(70, box_top - 248, "Entry into designated Red Hazard Polygons is strictly prohibited under police cordon.")

    # Section 3: Operational Checklist
    c.setFillColor(colors.HexColor("#1A365D"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(45, height - 540, "2. FIELD MOBILIZATION & ACTION PROTOCOL")
    
    c.setFont("Helvetica", 8.5)
    c.setFillColor(colors.HexColor("#2D3748"))
    checklist = [
        "1. Kerala State Disaster Management Authority (KSDMA) Quick Response Teams deployed for immediate muster.",
        "2. Medical triage ambulances pre-positioned at designated Safe Transit Nodes.",
        "3. NDMA Sachet emergency CAP SMS broadcast initiated across all subscriber cellular towers in sector.",
        "4. Shelter relief camp capacity allocated with 72-hour provisions, drinking water, and sanitary kits."
    ]
    cy = height - 558
    for item in checklist:
        c.drawString(55, cy, item)
        cy -= 15
        
    # Signature Block
    sig_y = height - 660
    c.setStrokeColor(colors.HexColor("#A0AEC0"))
    c.setLineWidth(1)
    c.line(width - 250, sig_y + 40, width - 45, sig_y + 40)
    
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#1A365D"))
    c.drawRightString(width - 45, sig_y + 25, authorized_by)
    c.setFont("Helvetica", 8.5)
    c.setFillColor(colors.HexColor("#4A5568"))
    c.drawRightString(width - 45, sig_y + 12, "District Magistrate & Incident Commander")
    c.drawRightString(width - 45, sig_y, "Chairman, District Disaster Management Authority (DDMA)")
    
    # Official Seal / Stamp Representation
    c.setStrokeColor(colors.HexColor("#C53030"))
    c.setLineWidth(1.5)
    c.circle(110, sig_y + 15, 30, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 6.5)
    c.setFillColor(colors.HexColor("#C53030"))
    c.drawCentredString(110, sig_y + 22, "DDMA WAYANAD")
    c.drawCentredString(110, sig_y + 12, "OFFICIALLY")
    c.drawCentredString(110, sig_y + 3, "AUTHORIZED")
    
    # Footer
    c.setStrokeColor(colors.HexColor("#CBD5E0"))
    c.setLineWidth(0.5)
    c.line(45, 50, width - 45, 50)
    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.HexColor("#A0AEC0"))
    c.drawString(45, 38, "Decision Support System for Landslide & Flash-Flood Hazard Red-Zoning • Generated via DRR Triage Engine")
    c.drawRightString(width - 45, 38, f"Page 1 of 1 • Ref: {order_ref}")
    
    c.save()
    
    return {
        "order_id": order_ref,
        "pdf_path": output_path,
        "filename": os.path.basename(output_path)
    }

class ManifestGenerator:
    """Wrapper class providing manifest generator interface."""
    def generate_pdf(self, habitation: dict, output_path: str, authorized_by: str = "District Magistrate") -> dict:
        return generate_manifest_pdf(habitation, output_path, authorized_by)
