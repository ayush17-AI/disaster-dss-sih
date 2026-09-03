class CAPAlertBuilder:
    """NDMA Sachet/CAP XML and SMS alert builder service."""
    def build_cap_xml(self, alert_id: str, sender: str, headline: str, description: str, area_desc: str) -> str:
        return f"<alert xmlns='urn:oasis:names:tc:emergency:cap:1.2'><identifier>{alert_id}</identifier><info><headline>{headline}</headline></info></alert>"
