import os
from pathlib import Path
from typing import Optional, Dict, Any
import qrcode
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Circle, Rect, String as DString
from reportlab.lib.colors import HexColor

from app.config import settings

THEMES = {
    "classic_gold": {
        "primary": HexColor("#1E293B"),       # Slate 800
        "accent": HexColor("#D97706"),        # Amber/Gold 600
        "border_outer": HexColor("#0F172A"),  # Slate 900
        "border_inner": HexColor("#B45309"),  # Gold border
        "bg_color": HexColor("#FFFBEB"),      # Warm parchment
        "subtext": HexColor("#475569"),       # Slate 600
        "seal_color": HexColor("#B45309")
    },
    "sapphire_modern": {
        "primary": HexColor("#0F172A"),       # Slate 900
        "accent": HexColor("#2563EB"),        # Royal Blue
        "border_outer": HexColor("#1E3A8A"),  # Deep Blue
        "border_inner": HexColor("#3B82F6"),  # Bright Blue
        "bg_color": HexColor("#F8FAFC"),      # Cool White
        "subtext": HexColor("#64748B"),       # Slate 500
        "seal_color": HexColor("#1D4ED8")
    },
    "emerald_academic": {
        "primary": HexColor("#064E3B"),       # Deep Emerald
        "accent": HexColor("#059669"),        # Emerald Green
        "border_outer": HexColor("#022C22"),  # Dark Spruce
        "border_inner": HexColor("#10B981"),  # Bright Emerald
        "bg_color": HexColor("#F0FDF4"),      # Mint tint
        "subtext": HexColor("#374151"),       # Charcoal
        "seal_color": HexColor("#047857")
    }
}

class CertificateGenerator:
    """
    Generates high-resolution, vector-based PDF certificates
    with custom ornamental borders, dynamic metadata, and verification QR codes.
    """

    @staticmethod
    def generate_qr_code(certificate_id: str, verification_url: str) -> str:
        """Generates a QR code linking to public verification endpoint."""
        qr_filename = f"qr_{certificate_id}.png"
        qr_path = settings.QR_CODES_DIR / qr_filename
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(verification_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0F172A", back_color="white")
        img.save(str(qr_path))
        return str(qr_path)

    @classmethod
    def generate_pdf(
        cls,
        certificate_id: str,
        recipient_name: str,
        recipient_email: str,
        event_title: str,
        issuer_name: str,
        signatory_name: Optional[str] = None,
        signatory_title: Optional[str] = None,
        issue_date: Optional[str] = None,
        template_theme: str = "classic_gold",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Builds and saves the landscape certificate PDF.
        Returns the absolute filepath of the generated PDF.
        """
        # Safety check for test failure injection or invalid data
        if recipient_name.strip() == "FAIL_TEST_RECIPIENT":
            raise ValueError("Deliberate failure triggered for testing isolation")

        theme = THEMES.get(template_theme, THEMES["classic_gold"])
        
        # Paths
        pdf_filename = f"cert_{certificate_id}.pdf"
        pdf_path = settings.CERTIFICATES_DIR / pdf_filename

        # Page Dimensions (Landscape Letter = 792 x 612 pt)
        page_width, page_height = landscape(letter)
        c = canvas.Canvas(str(pdf_path), pagesize=(page_width, page_height))
        c.setTitle(f"Certificate - {recipient_name}")

        # 1. Background fill
        c.setFillColor(theme["bg_color"])
        c.rect(0, 0, page_width, page_height, fill=True, stroke=False)

        # 2. Outer Ornamental Border
        c.setStrokeColor(theme["border_outer"])
        c.setLineWidth(4)
        c.rect(20, 20, page_width - 40, page_height - 40, fill=False, stroke=True)

        # 3. Inner Decorative Border with margin
        c.setStrokeColor(theme["border_inner"])
        c.setLineWidth(1.5)
        c.rect(26, 26, page_width - 52, page_height - 52, fill=False, stroke=True)

        # Corner Accents
        c.setStrokeColor(theme["accent"])
        c.setLineWidth(2)
        corner_size = 25
        # Top Left
        c.line(32, page_height - 32, 32 + corner_size, page_height - 32)
        c.line(32, page_height - 32, 32, page_height - 32 - corner_size)
        # Top Right
        c.line(page_width - 32, page_height - 32, page_width - 32 - corner_size, page_height - 32)
        c.line(page_width - 32, page_height - 32, page_width - 32, page_height - 32 - corner_size)
        # Bottom Left
        c.line(32, 32, 32 + corner_size, 32)
        c.line(32, 32, 32, 32 + corner_size)
        # Bottom Right
        c.line(page_width - 32, 32, page_width - 32 - corner_size, 32)
        c.line(page_width - 32, 32, page_width - 32, 32 + corner_size)

        # 4. Header / Issuer Organization
        c.setFillColor(theme["accent"])
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(page_width / 2.0, page_height - 75, issuer_name.upper())

        # 5. Certificate Title
        c.setFillColor(theme["primary"])
        c.setFont("Times-Bold", 32)
        c.drawCentredString(page_width / 2.0, page_height - 118, "CERTIFICATE OF COMPLETION")

        # Decorative separator under title
        c.setStrokeColor(theme["accent"])
        c.setLineWidth(1.5)
        c.line(page_width / 2.0 - 140, page_height - 128, page_width / 2.0 + 140, page_height - 128)
        c.circle(page_width / 2.0, page_height - 128, 3, fill=True, stroke=True)

        # 6. Presentation Line
        c.setFillColor(theme["subtext"])
        c.setFont("Helvetica", 12)
        c.drawCentredString(page_width / 2.0, page_height - 165, "THIS IS PROUDLY PRESENTED TO")

        # 7. Recipient Name
        c.setFillColor(theme["primary"])
        c.setFont("Times-BoldItalic", 34)
        c.drawCentredString(page_width / 2.0, page_height - 215, recipient_name)

        # Underline under name
        name_width = min(len(recipient_name) * 16, 450)
        c.setStrokeColor(theme["accent"])
        c.setLineWidth(1)
        c.line(page_width / 2.0 - (name_width / 2.0), page_height - 225, page_width / 2.0 + (name_width / 2.0), page_height - 225)

        # 8. Description Text
        c.setFillColor(theme["subtext"])
        c.setFont("Helvetica", 12)
        c.drawCentredString(
            page_width / 2.0,
            page_height - 260,
            "for successfully completing all requirements and demonstrating proficiency in"
        )

        # 9. Course / Event Title
        c.setFillColor(theme["accent"])
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(page_width / 2.0, page_height - 295, event_title)

        # 10. Additional Metadata (Grade / Score / Hours)
        if metadata and isinstance(metadata, dict):
            meta_items = [f"{k.capitalize()}: {v}" for k, v in metadata.items() if v]
            if meta_items:
                c.setFillColor(theme["subtext"])
                c.setFont("Helvetica-Bold", 11)
                meta_text = "   •   ".join(meta_items)
                c.drawCentredString(page_width / 2.0, page_height - 325, meta_text)

        # 11. Date and Verification QR Code
        verification_url = f"{settings.BASE_URL}/verify/{certificate_id}"
        qr_file = cls.generate_qr_code(certificate_id, verification_url)
        
        # Draw QR code in bottom center-left or bottom center
        qr_size = 75
        qr_x = 70
        qr_y = 65
        c.drawImage(qr_file, qr_x, qr_y, width=qr_size, height=qr_size)

        c.setFillColor(theme["subtext"])
        c.setFont("Helvetica", 8)
        c.drawString(qr_x, qr_y - 12, "Scan to Verify Authenticity")
        c.drawString(qr_x, qr_y - 22, f"ID: {certificate_id}")

        # 12. Golden Seal Emblem in Center
        seal_x = page_width / 2.0
        seal_y = 105
        c.setStrokeColor(theme["seal_color"])
        c.setFillColor(theme["seal_color"])
        c.circle(seal_x, seal_y, 30, fill=False, stroke=True)
        c.circle(seal_x, seal_y, 26, fill=False, stroke=True)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(seal_x, seal_y + 8, "OFFICIAL")
        c.drawCentredString(seal_x, seal_y - 3, "CREDENTIAL")
        c.drawCentredString(seal_x, seal_y - 14, "★ VERIFIED ★")

        # 13. Signatory Details (Right Side)
        sign_x = page_width - 200
        sign_y = 95
        
        # Signature line
        c.setStrokeColor(theme["primary"])
        c.setLineWidth(1)
        c.line(sign_x - 70, sign_y + 20, sign_x + 70, sign_y + 20)

        # Signatory Name & Title
        s_name = signatory_name or settings.DEFAULT_SIGNATORY_NAME
        s_title = signatory_title or settings.DEFAULT_SIGNATORY_TITLE
        date_str = issue_date or "October 11, 2026"

        c.setFillColor(theme["primary"])
        c.setFont("Times-Italic", 16)
        c.drawCentredString(sign_x, sign_y + 30, s_name)  # Simulated cursive signature

        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(sign_x, sign_y + 5, s_name)

        c.setFillColor(theme["subtext"])
        c.setFont("Helvetica", 9)
        c.drawCentredString(sign_x, sign_y - 8, s_title)
        c.drawCentredString(sign_x, sign_y - 20, f"Issued: {date_str}")

        # Finalize and save PDF
        c.showPage()
        c.save()

        return str(pdf_path)
