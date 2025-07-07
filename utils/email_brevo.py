import os, sib_api_v3_sdk as brevo

_cfg = brevo.Configuration()
_cfg.api_key["api-key"] = os.getenv("BREVO_API_KEY")
_api = brevo.TransactionalEmailsApi(brevo.ApiClient(_cfg))

EMAIL_FROM   = os.getenv("EMAIL_FROM")
FRONTEND_URL = os.getenv("FRONTEND_URL")

def send_confirmation_email(to_email: str, token: str) -> None:
    url  = f"{FRONTEND_URL}/presentacion/pages/correo-confirmado/{token}"
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

    hora_inicio_str = details.get('hora_inicio').strftime('%H:%M') if details.get('hora_inicio') else 'N/A' # type: ignore
    hora_fin_str = details.get('hora_fin').strftime('%H:%M') if details.get('hora_fin') else 'N/A' # type: ignore

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

def send_form_email(to_email: str, file_content: bytes, filename: str, details: dict) -> None:
    """
    Envía un correo al profesional con el formulario adjunto.
    """
    html = f"""
        <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px; border-radius: 8px;">
            <h2 style="color: #4f46e5;">Nuevo Formulario Recibido</h2>
            <p>Hola {details.get('nombre_profesional', '')},</p>
            <p>El cliente <strong>{details.get('nombre_cliente', 'N/A')}</strong> ha completado y enviado el formulario para la sesión del <strong>{details.get('fecha_sesion', 'N/A')}</strong> a las <strong>{details.get('hora_inicio', 'N/A')}</strong>.</p>
            <p>Puedes encontrar el documento adjunto a este correo.</p>
            <br>
            <p>Saludos,</p>
            <p>El equipo de CommuConnect</p>
        </div>
    """
    
    import base64
    attachment_content = base64.b64encode(file_content).decode()

    email = brevo.SendSmtpEmail(
        sender={"email": EMAIL_FROM, "name": "CommuConnect"},
        to=[{"email": to_email}],
        subject=f"Nuevo Formulario Recibido de {details.get('nombre_cliente', 'N/A')}",
        html_content=html,
        attachment=[
            {"content": attachment_content, "name": filename}
        ]
    )
    _api.send_transac_email(email)


def send_reset_link_email(to_email: str, nombre: str, reset_url: str) -> None:
    html = f"""
      <h2>Recuperación de Contraseña</h2>
      <p>Hola {nombre},</p>
      <p>Has solicitado restablecer tu contraseña. Para continuar, haz clic en el siguiente botón:</p>
      <p><a style="padding:10px 18px;background:#4f46e5;color:#fff;
         border-radius:6px;text-decoration:none" href="{reset_url}">
         Cambiar contraseña</a></p>
      <p>Este enlace tiene una validez de 5 minutos.</p>
      <p>Si el botón no funciona, también puedes copiar y pegar este enlace en tu navegador:</p>
      <p><code>{reset_url}</code></p>
      <p>Si tú no hiciste esta solicitud, puedes ignorar este mensaje.</p>
      <br>
      <p>El equipo de CommuConnect</p>
    """
    ...


    email = brevo.SendSmtpEmail(
        sender={"email": EMAIL_FROM, "name": "CommuConnect"},
        to=[{"email": to_email}],
        subject="Recuperación de Contraseña",
        html_content=html,
    )
    _api.send_transac_email(email)


def send_password_changed_email(to_email: str, nombre: str) -> None:
    html = f"""
      <h2>Confirmación de Cambio de Contraseña</h2>
      <p>Hola {nombre},</p>
      <p>Te informamos que tu contraseña fue cambiada exitosamente.</p>
      <p>Si tú realizaste este cambio, no necesitas hacer nada más.</p>
      <p>Si <strong>no reconoces esta actividad</strong>, por favor comunícate inmediatamente con nuestro equipo de soporte.</p>
      <br>
      <p>El equipo de CommuConnect</p>
    """

    email = brevo.SendSmtpEmail(
        sender={"email": EMAIL_FROM, "name": "CommuConnect"},
        to=[{"email": to_email}],
        subject="Confirmación de Cambio de Contraseña",
        html_content=html,
    )
    _api.send_transac_email(email)

def send_reservation_cancel_email(to_email: str, details: dict) -> None:
    html = f"""
        <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: auto; border: 1px solid #ddd; padding: 20px; border-radius: 8px;">
            <h2 style="color: #e53e3e;">Reserva Cancelada</h2>
            <p>Hola {details.get('nombre_cliente', '')},</p>
            <p>Te informamos que tu reserva para el servicio <strong>{details.get('nombre_servicio', 'N/A')}</strong> el día <strong>{details.get('fecha', 'N/A')}</strong> ha sido <strong>cancelada exitosamente</strong>.</p>
            <p>Si tienes dudas o necesitas reprogramar, contáctanos.</p>
            <br>
            <p>El equipo de CommuConnect</p>
        </div>
    """
    email = brevo.SendSmtpEmail(
        sender={"email": EMAIL_FROM, "name": "CommuConnect"},
        to=[{"email": to_email}],
        subject="Tu reserva ha sido cancelada",
        html_content=html,
    )
    _api.send_transac_email(email)

def send_suspension_accepted_email(to_email: str, details: dict) -> None:
    html = f"""
        <h2>¡Solicitud de suspensión aceptada!</h2>
        <p>Hola {details.get('nombre_usuario', '')},</p>
        <p>Tu solicitud de suspensión de membresía ha sido <strong>aceptada</strong>.</p>
        <ul>
            <li><strong>Motivo:</strong> {details.get('motivo', '')}</li>
            <li><strong>Fecha de inicio:</strong> {details.get('fecha_inicio', '')}</li>
            <li><strong>Fecha de fin:</strong> {details.get('fecha_fin', '')}</li>
        </ul>
        <p>Durante este periodo, tu membresía estará congelada.</p>
        <p>Gracias por confiar en CommuConnect.</p>
    """
    email = brevo.SendSmtpEmail(
        sender={"email": EMAIL_FROM, "name": "CommuConnect"},
        to=[{"email": to_email}],
        subject="Tu suspensión de membresía ha sido aceptada",
        html_content=html,
    )
    _api.send_transac_email(email)

def send_membership_activated_email(to_email: str, details: dict) -> None:
    html = f"""
        <h2>¡Membresía activada!</h2>
        <p>Hola {details.get('nombre_usuario', '')},</p>
        <p>Tu membresía <strong>{details.get('nombre_plan', '')}</strong> en la comunidad <strong>{details.get('nombre_comunidad', '')}</strong> está <strong>activa y lista para usar</strong>.</p>
        <ul>
            <li><strong>Fecha de inicio:</strong> {details.get('fecha_inicio', '')}</li>
            <li><strong>Fecha de fin:</strong> {details.get('fecha_fin', '')}</li>
            <li><strong>Precio:</strong> S/ {details.get('precio', '')}</li>
        </ul>
        <p>¡Disfruta de todos los beneficios de tu membresía!</p>
        <p>El equipo de CommuConnect</p>
    """
    email = brevo.SendSmtpEmail(
        sender={"email": EMAIL_FROM, "name": "CommuConnect"},
        to=[{"email": to_email}],
        subject="¡Tu membresía está activa!",
        html_content=html,
    )
    _api.send_transac_email(email)

def send_membership_cancelled_email(to_email: str, details: dict) -> None:
    html = f"""
        <h2>Membresía cancelada</h2>
        <p>Hola {details.get('nombre_usuario', '')},</p>
        <p>Te informamos que tu membresía <strong>{details.get('nombre_plan', '')}</strong> en la comunidad <strong>{details.get('nombre_comunidad', '')}</strong> ha sido <strong>cancelada</strong>.</p>
        <ul>
            <li><strong>Fecha de inicio:</strong> {details.get('fecha_inicio', '')}</li>
            <li><strong>Fecha de cancelación:</strong> {details.get('fecha_cancelacion', '')}</li>
        </ul>
        <p>Si tienes dudas o deseas reactivar tu membresía, contáctanos.</p>
        <p>El equipo de CommuConnect</p>
    """
    email = brevo.SendSmtpEmail(
        sender={"email": EMAIL_FROM, "name": "CommuConnect"},
        to=[{"email": to_email}],
        subject="Tu membresía ha sido cancelada",
        html_content=html,
    )
    _api.send_transac_email(email)