from io import BytesIO
import qrcode
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def generate_certificate_pdf(cert, user, course, out_path):
    page = landscape(A4)
    c = canvas.Canvas(out_path, pagesize=page)
    w, h = page

    c.setFillColor(colors.HexColor("#f8fafc"))
    c.rect(0, 0, w, h, fill=1, stroke=0)

    c.setStrokeColor(colors.HexColor("#2563eb"))
    c.setLineWidth(12)
    c.rect(20, 20, w - 40, h - 40)
    c.setStrokeColor(colors.HexColor("#f59e0b"))
    c.setLineWidth(2)
    c.rect(35, 35, w - 70, h - 70)

    c.setFillColor(colors.HexColor("#1e3a8a"))
    c.setFont("Helvetica-Bold", 40)
    c.drawCentredString(w / 2, h - 110, "Certificate of Completion")

    c.setStrokeColor(colors.HexColor("#f59e0b"))
    c.setLineWidth(3)
    c.line(w / 2 - 150, h - 130, w / 2 + 150, h - 130)

    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica", 16)
    c.drawCentredString(w / 2, h - 180, "This is to certify that")

    c.setFillColor(colors.HexColor("#2563eb"))
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(w / 2, h - 240, user.full_name or user.username)

    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica", 14)
    c.drawCentredString(w / 2, h - 280, "has successfully completed the course")

    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(w / 2, h - 320, course.title)

    c.setFont("Helvetica", 11)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawString(60, 60, f"Issued: {cert.issued_at.strftime('%B %d, %Y')}")
    c.drawString(60, 45, f"Certificate ID: {cert.code}")

    qr = qrcode.make(f"Certificate: {cert.code}")
    buf = BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)
    c.drawImage(ImageReader(buf), w - 130, 50, width=90, height=90)

    c.showPage()
    c.save()
    return out_path