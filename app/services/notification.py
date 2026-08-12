import logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Unifed premium APG responsive HTML template
EMAIL_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f8fafc;
            color: #1e293b;
            margin: 0;
            padding: 0;
            -webkit-font-smoothing: antialiased;
        }}
        .wrapper {{
            width: 100%;
            background-color: #f8fafc;
            padding: 20px 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
            border: 1px solid #e2e8f0;
        }}
        .header {{
            background-color: #1e2536;
            padding: 30px;
            text-align: center;
            border-bottom: 3px solid #3b82f6;
        }}
        .header h1 {{
            color: #ffffff;
            font-size: 22px;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }}
        .content {{
            padding: 40px 30px;
            line-height: 1.6;
        }}
        .content h2 {{
            color: #0f172a;
            font-size: 20px;
            margin-top: 0;
            margin-bottom: 20px;
        }}
        .content p {{
            margin-bottom: 20px;
            color: #475569;
        }}
        .code-box {{
            background-color: #f1f5f9;
            border-radius: 6px;
            padding: 20px;
            text-align: center;
            font-size: 32px;
            font-weight: 700;
            letter-spacing: 5px;
            color: #2563eb;
            border: 1px dashed #cbd5e1;
            margin: 25px 0;
        }}
        .btn {{
            display: inline-block;
            background-color: #3b82f6;
            color: #ffffff !important;
            text-decoration: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-weight: 600;
            margin: 10px 0;
            text-align: center;
        }}
        .footer {{
            background-color: #f8fafc;
            padding: 30px;
            border-top: 1px solid #e2e8f0;
            color: #64748b;
            font-size: 12px;
            line-height: 1.5;
        }}
        .signature {{
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #cbd5e1;
            color: #334155;
            font-weight: 600;
        }}
        .signature-title {{
            font-size: 13px;
            color: #475569;
            font-weight: 400;
            margin-top: 4px;
        }}
        .confidentiality {{
            margin-top: 20px;
            font-size: 11px;
            color: #94a3b8;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="wrapper">
        <div class="container">
            <div class="header">
                <h1>Adler Pelzer Group</h1>
            </div>
            <div class="content">
                <h2>{subtitle}</h2>
                {body_html}
            </div>
            <div class="footer">
                <div class="signature">
                    Adler Pelzer Group — Puebla Plant
                    <div class="signature-title">{footer_dept}</div>
                    <div class="signature-title">{footer_sys}</div>
                </div>
                <div class="confidentiality">
                    {footer_conf}
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

EMAIL_TRANSLATIONS = {
    "es": {
        "footer_dept": "Departamento de Calidad & Ingeniería de Procesos",
        "footer_sys": "Sistema de Gestión FMEA & Plan de Control",
        "footer_conf": "AVISO DE CONFIDENCIALIDAD: Este correo electrónico contiene información de carácter privilegiado y confidencial exclusiva para Adler Pelzer Group y sus destinatarios autorizados. Si usted no es el destinatario, queda estrictamente prohibida su difusión, copia o distribución.",
        "otp_subject": "Código de Verificación OTP - PFMEA",
        "otp_subtitle": "Verificación de Seguridad — Código OTP",
        "otp_body": """
    <p>Hemos recibido una solicitud de inicio de sesión para tu cuenta en el Portal Industrial PFMEA.</p>
    <p>Utiliza el siguiente código de un solo uso (OTP) para completar tu autenticación. Este código es estrictamente personal y expira en <strong>5 minutos</strong>:</p>
    <div class="code-box">{otp_code}</div>
    <p>Si no has solicitado este acceso, por favor ponte en contacto de inmediato con el Administrador de Sistemas de la planta APG Puebla.</p>
    """,
        "reset_pwd_subject": "Restablecer Contraseña - PFMEA",
        "reset_pwd_subtitle": "Restablecimiento de Contraseña — Código OTP",
        "reset_pwd_body": """
    <p>Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en el Portal Industrial PFMEA.</p>
    <p>Utiliza el siguiente código de verificación (OTP) para confirmar tu identidad y establecer tu nueva contraseña. Este código expira en <strong>5 minutos</strong>:</p>
    <div class="code-box">{otp_code}</div>
    <p>Si no has solicitado restablecer tu contraseña, puedes ignorar este correo. Tus credenciales siguen siendo seguras.</p>
    """,
        "temp_pwd_subject": "Nueva Contraseña Temporal - PFMEA",
        "temp_pwd_subtitle": "Restablecimiento Obligatorio de Contraseña",
        "temp_pwd_body": """
    <p>Se ha generado una nueva contraseña temporal segura para tu acceso al Portal Industrial PFMEA.</p>
    <p>Tu contraseña temporal de inicio de sesión es:</p>
    <div class="code-box" style="font-size: 20px; letter-spacing: 1px; color: #ef4444; font-family: monospace;">{temp_password}</div>
    <p>Para validar tu identidad y completar tu primer inicio de sesión obligatorio (donde deberás cambiar esta contraseña de inmediato), utiliza el siguiente código de verificación OTP:</p>
    <div class="code-box">{otp_code}</div>
    <p>Esta contraseña y código expiran en 5 minutos. Recuerda que nunca debes compartir tus credenciales de planta con terceros.</p>
    """,
        "welcome_subject": "Bienvenido a PFMEA - Verificación de Cuenta",
        "welcome_subtitle": "Bienvenido al Sistema PFMEA — Verificación Requerida",
        "welcome_body": """
    <p>Has sido registrado exitosamente en el Portal Industrial PFMEA. Como parte de nuestras normativas de seguridad (TISAX), requerimos verificar tu dirección de correo electrónico.</p>
    
    <p><strong>Detalles de tu cuenta:</strong></p>
    <ul>
        <li><strong>Rol asignado:</strong> {role_name}</li>
        <li><strong>Departamento:</strong> {department_name}</li>
    </ul>

    <p>Tu contraseña temporal de inicio de sesión generada por el sistema es:</p>
    <div class="code-box" style="font-size: 20px; letter-spacing: 1px; color: #ef4444; font-family: monospace;">{temp_password}</div>

    <p><strong>Paso 1:</strong> Verifica tu cuenta haciendo clic en el siguiente enlace:</p>
    <p style="text-align: center;">
        <a href="{verification_link}" class="btn">Verificar mi Cuenta</a>
    </p>

    <p><strong>Paso 2:</strong> Una vez verificado, inicia sesión con tu correo electrónico y la contraseña temporal proporcionada. Al iniciar sesión, se te requerirá actualizar esta contraseña inmediatamente.</p>
    <p>Recuerda que nunca debes compartir tus credenciales de planta con terceros.</p>
    """,
        "fallback_text": "Este correo contiene formato HTML. Por favor, use un cliente compatible.",
        "btn_verify": "Verificar mi Cuenta"
    },
    "en": {
        "footer_dept": "Quality & Process Engineering Department",
        "footer_sys": "FMEA & Control Plan Management System",
        "footer_conf": "CONFIDENTIALITY NOTICE: This email contains privileged and confidential information exclusively for Adler Pelzer Group and its authorized recipients. If you are not the intended recipient, its dissemination, copying or distribution is strictly prohibited.",
        "otp_subject": "OTP Verification Code - PFMEA",
        "otp_subtitle": "Security Verification — OTP Code",
        "otp_body": """
    <p>We have received a login request for your account in the PFMEA Industrial Portal.</p>
    <p>Use the following one-time password (OTP) to complete your authentication. This code is strictly personal and expires in <strong>5 minutes</strong>:</p>
    <div class="code-box">{otp_code}</div>
    <p>If you did not request this access, please contact the Systems Administrator of the APG Puebla plant immediately.</p>
    """,
        "reset_pwd_subject": "Password Reset - PFMEA",
        "reset_pwd_subtitle": "Password Reset — OTP Code",
        "reset_pwd_body": """
    <p>We have received a request to reset the password for your account in the PFMEA Industrial Portal.</p>
    <p>Use the following verification code (OTP) to confirm your identity and set your new password. This code expires in <strong>5 minutes</strong>:</p>
    <div class="code-box">{otp_code}</div>
    <p>If you did not request a password reset, you can ignore this email. Your credentials remain safe.</p>
    """,
        "temp_pwd_subject": "New Temporary Password - PFMEA",
        "temp_pwd_subtitle": "Mandatory Password Reset",
        "temp_pwd_body": """
    <p>A new secure temporary password has been generated for your access to the PFMEA Industrial Portal.</p>
    <p>Your temporary login password is:</p>
    <div class="code-box" style="font-size: 20px; letter-spacing: 1px; color: #ef4444; font-family: monospace;">{temp_password}</div>
    <p>To validate your identity and complete your mandatory first login (where you must change this password immediately), use the following OTP verification code:</p>
    <div class="code-box">{otp_code}</div>
    <p>This password and code expire in 5 minutes. Remember that you must never share your plant credentials with third parties.</p>
    """,
        "welcome_subject": "Welcome to PFMEA - Account Verification",
        "welcome_subtitle": "Welcome to the PFMEA System — Verification Required",
        "welcome_body": """
    <p>You have been successfully registered in the PFMEA Industrial Portal. As part of our security regulations (TISAX), we are required to verify your email address.</p>
    
    <p><strong>Account details:</strong></p>
    <ul>
        <li><strong>Assigned role:</strong> {role_name}</li>
        <li><strong>Department:</strong> {department_name}</li>
    </ul>

    <p>Your temporary login password generated by the system is:</p>
    <div class="code-box" style="font-size: 20px; letter-spacing: 1px; color: #ef4444; font-family: monospace;">{temp_password}</div>

    <p><strong>Step 1:</strong> Verify your account by clicking on the following link:</p>
    <p style="text-align: center;">
        <a href="{verification_link}" class="btn">{btn_verify}</a>
    </p>

    <p><strong>Step 2:</strong> Once verified, log in with your email and the provided temporary password. Upon logging in, you will be required to update this password immediately.</p>
    <p>Remember that you must never share your plant credentials with third parties.</p>
    """,
        "fallback_text": "This email contains HTML formatting. Please use a compatible client.",
        "btn_verify": "Verify my Account"
    }
}

# ─── Team Assignment Notification Templates ───────────────────────────────────

TEAM_ASSIGN_TEMPLATES = {
    "es": {
        "subject": "[NUEVA ASIGNACIÓN] Proyecto PFMEA — {project_name}",
        "subtitle": "Asignación a Equipo Multidisciplinario",
        "body": """
    <p>Estimado(a) <strong>{recipient_name}</strong>,</p>
    <p>Has sido asignado a un nuevo equipo multidisciplinario para el desarrollo y control de un documento PFMEA en la plataforma APG.</p>
    
    <table style="width:100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
      <tr style="background-color: #fef3c7;">
        <td style="padding: 10px 14px; border: 1px solid #fcd34d; font-weight: 600; width: 40%;">📁 Proyecto</td>
        <td style="padding: 10px 14px; border: 1px solid #fcd34d;">{project_name}</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">🆔 ID Documento</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-family: monospace;">{pfmea_id}</td>
      </tr>
      <tr style="background-color: #f8fafc;">
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">📦 No. de Parte</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0;">{part_number}</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">🏢 Cliente</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0;">{customer}</td>
      </tr>
      <tr style="background-color: #f8fafc;">
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">👤 Tu Rol</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0;">{role_in_team}</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">🏢 Departamento</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0;">{department}</td>
      </tr>
    </table>

    <div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 14px 18px; margin: 20px 0; border-radius: 4px;">
      <p style="margin: 0; color: #1e3a8a; font-weight: 600;">ℹ️ Acciones Recomendadas</p>
      <ul style="margin: 8px 0 0; color: #1e3a8a;">
        <li>Accede a la plataforma para revisar el estatus del documento.</li>
        <li>Familiarízate con las características del proceso.</li>
        <li>Si consideras que esta asignación es un error, contacta al administrador.</li>
      </ul>
    </div>
    <p style="text-align: center; margin-top: 30px;">
        <a href="{link}" class="btn">Abrir Documento PFMEA</a>
    </p>
    """
    },
    "en": {
        "subject": "[NEW ASSIGNMENT] PFMEA Project — {project_name}",
        "subtitle": "Multidisciplinary Team Assignment",
        "body": """
    <p>Dear <strong>{recipient_name}</strong>,</p>
    <p>You have been assigned to a new multidisciplinary team for the development and control of a PFMEA document on the APG platform.</p>
    
    <table style="width:100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
      <tr style="background-color: #fef3c7;">
        <td style="padding: 10px 14px; border: 1px solid #fcd34d; font-weight: 600; width: 40%;">📁 Project</td>
        <td style="padding: 10px 14px; border: 1px solid #fcd34d;">{project_name}</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">🆔 Document ID</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-family: monospace;">{pfmea_id}</td>
      </tr>
      <tr style="background-color: #f8fafc;">
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">📦 Part Number</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0;">{part_number}</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">🏢 Customer</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0;">{customer}</td>
      </tr>
      <tr style="background-color: #f8fafc;">
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">👤 Your Role</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0;">{role_in_team}</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">🏢 Department</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0;">{department}</td>
      </tr>
    </table>

    <div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 14px 18px; margin: 20px 0; border-radius: 4px;">
      <p style="margin: 0; color: #1e3a8a; font-weight: 600;">ℹ️ Recommended Actions</p>
      <ul style="margin: 8px 0 0; color: #1e3a8a;">
        <li>Access the platform to review the document status.</li>
        <li>Familiarize yourself with the process characteristics.</li>
        <li>If you believe this assignment is an error, contact the administrator.</li>
      </ul>
    </div>
    <p style="text-align: center; margin-top: 30px;">
        <a href="{link}" class="btn">Open PFMEA Document</a>
    </p>
    """
    }
}

# ─── Archive Notification Templates ───────────────────────────────────────────

ARCHIVE_TEMPLATES = {
    "es": {
        "subject": "[ACCIÓN REQUERIDA] Documento Archivado — {doc_title}",
        "subtitle": "Notificación de Ciclo de Vida: Documento Obsoleto",
        "body": """
    <p>Estimado(a) <strong>{recipient_name}</strong>,</p>
    <p>Te informamos que el siguiente documento ha sido <strong style="color: #d97706;">ARCHIVADO</strong> 
    y movido al repositorio histórico de la plataforma APG PFMEA DMS.</p>

    <table style="width:100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
      <tr style="background-color: #fef3c7;">
        <td style="padding: 10px 14px; border: 1px solid #fcd34d; font-weight: 600; width: 40%;">📄 Documento</td>
        <td style="padding: 10px 14px; border: 1px solid #fcd34d;">{doc_title}</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">🆔 ID Documento</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-family: monospace;">{doc_code}</td>
      </tr>
      <tr style="background-color: #f8fafc;">
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">📋 Versión</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0;">v{doc_version}</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">👤 Archivado por</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0;">{archived_by}</td>
      </tr>
      <tr style="background-color: #f8fafc;">
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">📅 Fecha de Archivado</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0;">{archived_at}</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">📝 Motivo del Cambio</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0;">{change_reason}</td>
      </tr>
      {eco_row_es}
    </table>

    <div style="background-color: #fef3c7; border-left: 4px solid #d97706; padding: 14px 18px; margin: 20px 0; border-radius: 4px;">
      <p style="margin: 0; color: #92400e; font-weight: 600;">⚠️ Acciones Requeridas</p>
      <ul style="margin: 8px 0 0; color: #92400e;">
        <li>Este documento ya <strong>no está disponible</strong> para edición en las terminales de planta.</li>
        <li>Si estás ligado a este documento (PFMEA, Plan de Control), <strong>revisa el estado de tus documentos vinculados</strong>.</li>
        <li>Si consideras que este archivado es un error, contacta al Administrador del sistema.</li>
      </ul>
    </div>
    <p style="color: #64748b; font-size: 13px;">Este es un mensaje automático del Sistema de Gestión de Documentos APG PFMEA. Por favor no respondas a este correo.</p>
    """,
        "eco_row": """<tr style="background-color: #f8fafc;">
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">🔧 Número ECO</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-family: monospace;">{eco_number}</td>
      </tr>""",
    },
    "en": {
        "subject": "[ACTION REQUIRED] Document Archived — {doc_title}",
        "subtitle": "Lifecycle Notification: Document Obsolete",
        "body": """
    <p>Dear <strong>{recipient_name}</strong>,</p>
    <p>We inform you that the following document has been <strong style="color: #d97706;">ARCHIVED</strong> 
    and moved to the historical repository of the APG PFMEA DMS platform.</p>

    <table style="width:100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
      <tr style="background-color: #fef3c7;">
        <td style="padding: 10px 14px; border: 1px solid #fcd34d; font-weight: 600; width: 40%;">📄 Document</td>
        <td style="padding: 10px 14px; border: 1px solid #fcd34d;">{doc_title}</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">🆔 Document ID</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-family: monospace;">{doc_code}</td>
      </tr>
      <tr style="background-color: #f8fafc;">
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">📋 Version</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0;">v{doc_version}</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">👤 Archived By</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0;">{archived_by}</td>
      </tr>
      <tr style="background-color: #f8fafc;">
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">📅 Archive Date</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0;">{archived_at}</td>
      </tr>
      <tr>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">📝 Change Reason</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0;">{change_reason}</td>
      </tr>
      {eco_row_en}
    </table>

    <div style="background-color: #fef3c7; border-left: 4px solid #d97706; padding: 14px 18px; margin: 20px 0; border-radius: 4px;">
      <p style="margin: 0; color: #92400e; font-weight: 600;">⚠️ Required Actions</p>
      <ul style="margin: 8px 0 0; color: #92400e;">
        <li>This document is <strong>no longer available</strong> for editing on plant terminals.</li>
        <li>If you are linked to this document (PFMEA, Control Plan), <strong>review the status of your linked documents</strong>.</li>
        <li>If you believe this archiving is an error, contact the System Administrator.</li>
      </ul>
    </div>
    <p style="color: #64748b; font-size: 13px;">This is an automated message from the APG PFMEA Document Management System. Please do not reply to this email.</p>
    """,
        "eco_row": """<tr style="background-color: #f8fafc;">
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-weight: 600;">🔧 ECO Number</td>
        <td style="padding: 10px 14px; border: 1px solid #e2e8f0; font-family: monospace;">{eco_number}</td>
      </tr>""",
    },
}


async def send_team_assign_notification_email(
    to_email: str,
    recipient_name: str,
    project_name: str,
    pfmea_id: str,
    part_number: str,
    customer: str,
    role_in_team: str,
    department: str,
    link: str,
    lang: str = "es",
) -> bool:
    """
    Send assignment notification to a user when added to a PFMEA team.
    """
    t = TEAM_ASSIGN_TEMPLATES.get(lang, TEAM_ASSIGN_TEMPLATES["es"])

    body_html = t["body"].format(
        recipient_name=recipient_name or "Usuario",
        project_name=project_name,
        pfmea_id=pfmea_id,
        part_number=part_number,
        customer=customer,
        role_in_team=role_in_team,
        department=department,
        link=link
    )
    subject = t["subject"].format(project_name=project_name)
    return await send_email(to_email, subject, t["subtitle"], body_html, lang)


async def send_archive_notification_email(
    team_emails: list[tuple[str, str]],  # list of (email, full_name)
    doc_title: str,
    doc_code: str,
    doc_version: int,
    archived_by: str,
    archived_at: str,
    change_reason: str,
    eco_number: str | None = None,
    lang: str = "es",
) -> bool:
    """
    Send archiving notification to all members of the multidisciplinary team.
    Uses the existing APG premium email template.
    """
    t = ARCHIVE_TEMPLATES.get(lang, ARCHIVE_TEMPLATES["es"])
    eco_row_key = "eco_row_es" if lang == "es" else "eco_row_en"

    eco_html = ""
    if eco_number:
        eco_html = t["eco_row"].format(eco_number=eco_number)

    all_succeeded = True
    for to_email, recipient_name in team_emails:
        body_html = t["body"].format(
            recipient_name=recipient_name or "Equipo",
            doc_title=doc_title,
            doc_code=doc_code,
            doc_version=doc_version,
            archived_by=archived_by,
            archived_at=archived_at,
            change_reason=change_reason,
            **{eco_row_key: eco_html},
        )
        subject = t["subject"].format(doc_title=doc_title)
        success = await send_email(to_email, subject, t["subtitle"], body_html, lang)
        if not success:
            all_succeeded = False

    return all_succeeded


import resend

async def send_email(to_email: str, subject: str, subtitle: str, body_html: str, lang: str = "en") -> bool:
    """
    Asynchronously send an email using Resend API.
    Includes a fallback that prints to console for easy local testing.
    """
    settings = get_settings()
    t = EMAIL_TRANSLATIONS.get(lang, EMAIL_TRANSLATIONS["en"])
    
    # 1. Format HTML using our responsive global template
    full_html = EMAIL_TEMPLATE.format(
        title=subject,
        subtitle=subtitle,
        body_html=body_html,
        footer_dept=t["footer_dept"],
        footer_sys=t["footer_sys"],
        footer_conf=t["footer_conf"]
    )
    
    # 2. Check if Resend API key exists, else fall back to console print
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured. Falling back to console notification print.")
        print("\n" + "="*80)
        print(f"📧 [NOTIFICATION MAIL FALLBACK]")
        print(f"TO: {to_email}")
        print(f"SUBJECT: {subject}")
        print(f"SUBTITLE: {subtitle}")
        print(f"BODY:\n{body_html.strip()}")
        print("="*80 + "\n")
        return True

    # 3. Send using Resend SDK
    resend.api_key = settings.RESEND_API_KEY
    
    try:
        params = {
            "from": f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>",
            "to": [to_email],
            "subject": subject,
            "html": full_html,
        }
        
        email_response = resend.Emails.send(params)
        logger.info(f"Notification email successfully sent to {to_email} via Resend.")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email} via Resend: {e}")
        # Log to console so developer doesn't lose the token
        print("\n" + "="*80)
        print(f"⚠️ [RESEND DELIVERY FAILED - NOTIFICATION PRINT]")
        print(f"TO: {to_email}")
        print(f"SUBJECT: {subject}")
        print(f"BODY:\n{body_html.strip()}")
        print("="*80 + "\n")
        return False

async def send_otp_email(to_email: str, otp_code: str, lang: str = "en") -> bool:
    """
    Send OTP verification email for two-phase login.
    """
    t = EMAIL_TRANSLATIONS.get(lang, EMAIL_TRANSLATIONS["en"])
    body_html = t["otp_body"].format(otp_code=otp_code)
    return await send_email(to_email, t["otp_subject"], t["otp_subtitle"], body_html, lang)

async def send_reset_password_otp_email(to_email: str, otp_code: str, lang: str = "en") -> bool:
    """
    Send OTP verification email for password reset.
    """
    t = EMAIL_TRANSLATIONS.get(lang, EMAIL_TRANSLATIONS["en"])
    body_html = t["reset_pwd_body"].format(otp_code=otp_code)
    return await send_email(to_email, t["reset_pwd_subject"], t["reset_pwd_subtitle"], body_html, lang)

async def send_temp_password_email(to_email: str, temp_password: str, otp_code: str, lang: str = "en") -> bool:
    """
    Send temporary password and OTP validation email for password reset requests.
    """
    t = EMAIL_TRANSLATIONS.get(lang, EMAIL_TRANSLATIONS["en"])
    body_html = t["temp_pwd_body"].format(temp_password=temp_password, otp_code=otp_code)
    return await send_email(to_email, t["temp_pwd_subject"], t["temp_pwd_subtitle"], body_html, lang)

async def send_welcome_email(to_email: str, temp_password: str, role_name: str, department_name: str, verification_link: str, lang: str = "en") -> bool:
    """
    Send a welcome email with static verification link, roles, and initial password.
    """
    t = EMAIL_TRANSLATIONS.get(lang, EMAIL_TRANSLATIONS["en"])
    
    # Translate specific department name placeholders if needed, otherwise use as is
    if lang == "en" and department_name == "Sin Departamento":
        department_name = "No Department"
        
    # Translate role name for display if necessary
    role_display = role_name
    if lang == "es":
        if role_name == "Administrator": role_display = "Administrador"
        elif role_name == "Viewer": role_display = "Visualizador"
        # Others like 'PFMEA Owner', 'Team Member' might stay English or be translated.

    body_html = t["welcome_body"].format(
        role_name=role_display,
        department_name=department_name,
        temp_password=temp_password,
        verification_link=verification_link,
        btn_verify=t["btn_verify"]
    )
    return await send_email(to_email, t["welcome_subject"], t["welcome_subtitle"], body_html, lang)
