class ManifestGenerator:
    """PDF / tabular relocation manifest generation service."""
    def generate_pdf(self, habitation_id: str, authorized_by: str) -> str:
        return f"/static/manifests/{habitation_id}_authorized.pdf"
