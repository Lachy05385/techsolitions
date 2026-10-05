from fastapi_mail import FastMail, MessageSchema, MessageType
from config import mail_config, settings

fm = FastMail(mail_config)


async def enviar_notificacion_lead(lead_data: dict):
    """
    Envía un correo a tu dirección con los datos del nuevo lead.
    """
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f4f4; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #00d4ff, #00ffa3); padding: 30px; text-align: center; }}
            .header h1 {{ color: #0a0e27; margin: 0; font-size: 24px; }}
            .content {{ padding: 30px; }}
            .field {{ margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #00d4ff; }}
            .field-label {{ font-weight: bold; color: #555; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }}
            .field-value {{ color: #0a0e27; font-size: 16px; margin-top: 5px; }}
            .descripcion {{ background: #fff3cd; border-left-color: #ffc107; }}
            .footer {{ text-align: center; padding: 20px; color: #888; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Nuevo Lead en Arquia</h1>
            </div>
            <div class="content">
                <div class="field">
                    <div class="field-label">Nombre</div>
                    <div class="field-value">{lead_data.get('nombre', 'N/A')}</div>
                </div>
                <div class="field">
                    <div class="field-label">Email</div>
                    <div class="field-value">{lead_data.get('email', 'N/A')}</div>
                </div>
                <div class="field">
                    <div class="field-label">Teléfono</div>
                    <div class="field-value">{lead_data.get('telefono', 'No proporcionado')}</div>
                </div>
                <div class="field">
                    <div class="field-label">Empresa</div>
                    <div class="field-value">{lead_data.get('empresa', 'No proporcionada')}</div>
                </div>
                <div class="field">
                    <div class="field-label">Servicio Solicitado</div>
                    <div class="field-value">{lead_data.get('servicio', 'N/A')}</div>
                </div>
                <div class="field">
                    <div class="field-label">Presupuesto</div>
                    <div class="field-value">{lead_data.get('presupuesto', 'No especificado')}</div>
                </div>
                <div class="field descripcion">
                    <div class="field-label">Descripción del Proyecto</div>
                    <div class="field-value">{lead_data.get('descripcion', 'N/A')}</div>
                </div>
            </div>
            <div class="footer">
                <p>Recibido el {lead_data.get('fecha_creacion', '')}</p>
                <p>Arquia — Llevamos tus ideas al mundo digital</p>
            </div>
        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject=f"🚀 Nuevo Lead: {lead_data.get('nombre')} - {lead_data.get('servicio')}",
        recipients=[settings.NOTIFICATION_EMAIL],
        body=html_body,
        subtype=MessageType.html,
    )

    await fm.send_message(message)