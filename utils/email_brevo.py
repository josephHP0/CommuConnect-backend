import os, sib_api_v3_sdk as brevo

_cfg = brevo.Configuration()
_cfg.api_key["api-key"] = os.getenv("BREVO_API_KEY")
_api = brevo.TransactionalEmailsApi(brevo.ApiClient(_cfg))

EMAIL_FROM   = os.getenv("EMAIL_FROM")
FRONTEND_URL = os.getenv("FRONTEND_URL")

def send_confirmation_email(to_email: str, token: str) -> None:
    url  = f"{FRONTEND_URL}/confirmar/{token}"
    html = f"""
      <h2>¡Bienvenido a CommuConnect!</h2>
      <p>Pulsa el botón para activar tu cuenta:</p>
      <p><a style="padding:10px 18px;background:#4f46e5;color:#fff;
         border-radius:6px;text-decoration:none" href="{url}">
         Confirmar correo</a></p>
      <p>Si el botón no funciona, copia y pega este enlace:<br>{url}</p>
    """
    email = brevo.SendSmtpEmail(
        sender={"email": EMAIL_FROM, "name": "CommuConnect"},
        to=[{"email": to_email}],
        subject="Confirma tu correo",
        html_content=html,
    )
    _api.send_transac_email(email)