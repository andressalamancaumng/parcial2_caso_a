import pyotp
import qrcode
import io

class MFAService:
    def generate_secret(self):
        return pyotp.random_base32()
    def generate_qr_png(self, account_name, secret, issuer="Clinic"):
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=account_name, issuer_name=issuer)
        img = qrcode.make(uri)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    def verify_otp(self, secret, code):
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)