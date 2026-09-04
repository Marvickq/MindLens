import io
import base64
import qrcode
from qrcode.image.pil import PilImage


def generate_qr_payload(intake_url: str) -> dict:
    """Return the intake URL and a base64-encoded PNG QR code."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=2,
    )
    qr.add_data(intake_url)
    qr.make(fit=True)

    img: PilImage = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    return {
        "url": intake_url,
        "qr_base64": f"data:image/png;base64,{b64}",
    }
