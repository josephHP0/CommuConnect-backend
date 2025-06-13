import os, sib_api_v3_sdk as brevo

_cfg = brevo.Configuration()
_cfg.api_key["api-key"] = os.getenv("BREVO_API_KEY")
_api = brevo.TransactionalEmailsApi(brevo.ApiClient(_cfg))

EMAIL_FROM   = os.getenv("EMAIL_FROM")
FRONTEND_URL = os.getenv("FRONTEND_URL")

def send_confirmation_email(to_email: str, token: str) -> None:
    url  = f"{FRONTEND_URL}/presentacion/correo-confirmado/{token}"
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

def send_reservation_email(to_email: str, details: dict) -> None:
    # Use .get() for optional fields to avoid KeyErrors
    direccion_detallada_html = f"<br><small style='color: #555;'>{details.get('direccion_detallada', '')}</small>" if details.get('direccion_detallada') else ""
    
    creditos_html = ""
    if details.get("topes_disponibles") is not None and details.get("topes_consumidos") is not None:
        creditos_html = f"""
            <p style="margin-top: 20px; border-top: 1px solid #eee; padding-top: 15px; font-size: 14px;">
                <strong>Resumen de tu plan:</strong> 
                Has utilizado {details['topes_consumidos']} de {details['topes_disponibles']} topes.
            </p>
        """

    hora_inicio_str = details.get('hora_inicio').strftime('%H:%M') if details.get('hora_inicio') else 'N/A'
    hora_fin_str = details.get('hora_fin').strftime('%H:%M') if details.get('hora_fin') else 'N/A'

    html = f"""
        <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px; border-radius: 8px;">
            <h2 style="color: #4f46e5;">Confirmación de Reserva en CommuConnect</h2>
            <p>Hola {details.get('nombre_cliente', '')},</p>
            <p>Tu reserva ha sido confirmada con éxito. Aquí están los detalles:</p>
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px;">
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 10px; border: 1px solid #eee; font-weight: bold;">Servicio:</td>
                    <td style="padding: 10px; border: 1px solid #eee;">{details.get('nombre_servicio', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #eee; font-weight: bold;">Fecha:</td>
                    <td style="padding: 10px; border: 1px solid #eee;">{details.get('fecha', 'N/A')}</td>
                </tr>
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 10px; border: 1px solid #eee; font-weight: bold;">Hora:</td>
                    <td style="padding: 10px; border: 1px solid #eee;">{hora_inicio_str} - {hora_fin_str}</td>
                </tr>
                <tr>
                    <td style="padding: 10px; border: 1px solid #eee; font-weight: bold;">Ubicación:</td>
                    <td style="padding: 10px; border: 1px solid #eee;">
                        {details.get('ubicacion', 'N/A')}
                        {direccion_detallada_html}
                    </td>
                </tr>
            </table>
            {creditos_html}
            <p style="margin-top: 25px;">¡Te esperamos!</p>
            <p>El equipo de CommuConnect</p>
        </div>
    """
    email = brevo.SendSmtpEmail(
        sender={"email": EMAIL_FROM, "name": "CommuConnect"},
        to=[{"email": to_email}],
        subject="Confirmación de tu Reserva",
        html_content=html,
    )
    _api.send_transac_email(email)