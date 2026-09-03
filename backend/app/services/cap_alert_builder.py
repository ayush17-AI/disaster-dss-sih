import time
from datetime import datetime
import lxml.etree as etree

NSMAP = {None: "urn:oasis:names:tc:emergency:cap:1.2"}

def build_cap_alert(habitation_name: str, message: str, lat: float, lon: float) -> str:
    """
    Generate an NDMA Sachet/CAP 1.2 compliant XML string for a given habitation.
    """
    clean_name = habitation_name.replace(" ", "_")
    identifier = f"DRR-{clean_name}-{int(time.time())}"
    sent_timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")
    
    root = etree.Element("alert", nsmap=NSMAP)
    
    # Root metadata elements
    etree.SubElement(root, "identifier").text = identifier
    etree.SubElement(root, "sender").text = "district-eoc@disaster-dss.gov.in"
    etree.SubElement(root, "sent").text = sent_timestamp
    etree.SubElement(root, "status").text = "Actual"
    etree.SubElement(root, "msgType").text = "Alert"
    etree.SubElement(root, "scope").text = "Public"
    
    # <info> child block
    info = etree.SubElement(root, "info")
    etree.SubElement(info, "category").text = "Geo"
    etree.SubElement(info, "event").text = "Landslide Risk Evacuation Advisory"
    etree.SubElement(info, "urgency").text = "Immediate"
    etree.SubElement(info, "severity").text = "Extreme"
    etree.SubElement(info, "certainty").text = "Observed"
    etree.SubElement(info, "headline").text = f"Preemptive Evacuation Advisory for {habitation_name}"
    etree.SubElement(info, "description").text = message
    
    # <area> block
    area = etree.SubElement(info, "area")
    etree.SubElement(area, "areaDesc").text = f"{habitation_name} Vicinity"
    etree.SubElement(area, "circle").text = f"{lat:.5f},{lon:.5f} 2.0"
    
    xml_bytes = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8")
    return xml_bytes.decode("utf-8")

def build_simulated_sms(habitation_name: str, message: str, recipient_count: int = 150) -> dict:
    """
    Generate simulated cellular broadcast/SMS dispatch payload.
    """
    return {
        "dispatched_count": recipient_count,
        "sms_text": message,
        "target": habitation_name,
        "status": "DELIVERED"
    }

class CAPAlertBuilder:
    """Wrapper class providing CAP Alert Builder interface."""
    def build_cap_xml(self, alert_id: str, sender: str, headline: str, description: str, area_desc: str) -> str:
        return build_cap_alert(area_desc, description, 11.54, 76.15)

    def build_alert(self, habitation_name: str, message: str, lat: float, lon: float) -> str:
        return build_cap_alert(habitation_name, message, lat, lon)

    def build_sms(self, habitation_name: str, message: str, recipient_count: int = 150) -> dict:
        return build_simulated_sms(habitation_name, message, recipient_count)
