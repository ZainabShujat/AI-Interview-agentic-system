import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    @staticmethod
    def send_email(to_email: str, subject: str, html_content: str):
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USERNAME")
        smtp_pass = os.getenv("SMTP_PASSWORD")
        
        if not smtp_user or not smtp_pass:
            print(f"[MOCK EMAIL] To: {to_email}")
            print(f"Subject: {subject}")
            print("Configure SMTP credentials to send real emails.")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"SmartHire AI <{smtp_user}>"
        msg["To"] = to_email

        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            print(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            print(f"Failed to send email to {to_email}: {str(e)}")
            return False

    @staticmethod
    def send_candidate_confirmation(candidate_name: str, candidate_email: str, role: str, date_str: str, time_str: str, meet_link: str):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="margin:0;padding:0;background:#f0f4f8;font-family:'Segoe UI',Arial,sans-serif;">
          <div style="max-width:600px;margin:40px auto;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
            <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6,#a855f7);padding:40px 32px;text-align:center;">
              <h1 style="color:#fff;margin:0;font-size:28px;">🎉 Interview Scheduled!</h1>
              <p style="color:rgba(255,255,255,0.9);margin:8px 0 0;font-size:16px;">HireIntel AI</p>
            </div>
            <div style="padding:32px;">
              <p style="font-size:18px;color:#1e293b;margin:0 0 24px;">Hi <strong>{candidate_name}</strong>,</p>
              <p style="font-size:15px;color:#475569;line-height:1.6;margin:0 0 24px;">
                Great news! Your interview has been successfully scheduled. Here are the details:
              </p>
              <div style="background:#f8fafc;border-radius:12px;padding:24px;margin:0 0 24px;border:1px solid #e2e8f0;">
                <table style="width:100%;border-collapse:collapse;">
                  <tr>
                    <td style="padding:8px 0;color:#64748b;font-size:14px;width:120px;">💼 Position</td>
                    <td style="padding:8px 0;color:#1e293b;font-size:14px;font-weight:600;">{role}</td>
                  </tr>
                  <tr>
                    <td style="padding:8px 0;color:#64748b;font-size:14px;">📅 Date</td>
                    <td style="padding:8px 0;color:#1e293b;font-size:14px;font-weight:600;">{date_str}</td>
                  </tr>
                  <tr>
                    <td style="padding:8px 0;color:#64748b;font-size:14px;">🕐 Time</td>
                    <td style="padding:8px 0;color:#1e293b;font-size:14px;font-weight:600;">{time_str}</td>
                  </tr>
                  <tr>
                    <td style="padding:8px 0;color:#64748b;font-size:14px;">📹 Platform</td>
                    <td style="padding:8px 0;color:#1e293b;font-size:14px;font-weight:600;">Zoom</td>
                  </tr>
                </table>
              </div>
              <div style="text-align:center;margin:0 0 24px;">
                <a href="{meet_link}" style="display:inline-block;background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff;text-decoration:none;padding:14px 40px;border-radius:10px;font-size:16px;font-weight:600;box-shadow:0 4px 12px rgba(99,102,241,0.3);">
                  Join Zoom Meeting 🔗
                </a>
              </div>
            </div>
            <div style="background:#f8fafc;padding:20px 32px;text-align:center;border-top:1px solid #e2e8f0;">
              <p style="margin:0;color:#94a3b8;font-size:12px;">Powered by HireIntel AI</p>
            </div>
          </div>
        </body>
        </html>
        """
        EmailService.send_email(candidate_email, f"✅ Interview Scheduled — {role} | {date_str} at {time_str}", html)

    @staticmethod
    def send_recruiter_notification(recruiter_email: str, candidate_name: str, candidate_email: str, role: str, date_str: str, time_str: str, meet_link: str):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="margin:0;padding:0;background:#f0f4f8;font-family:'Segoe UI',Arial,sans-serif;">
          <div style="max-width:600px;margin:40px auto;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
            <div style="background:linear-gradient(135deg,#059669,#10b981);padding:32px;text-align:center;">
              <h1 style="color:#fff;margin:0;font-size:24px;">📋 New Interview Scheduled</h1>
              <p style="color:rgba(255,255,255,0.9);margin:8px 0 0;font-size:14px;">HireIntel AI Notification</p>
            </div>
            <div style="padding:32px;">
              <p style="font-size:16px;color:#1e293b;margin:0 0 20px;">A new interview has been auto-scheduled by HireIntel AI:</p>
              <div style="background:#f0fdf4;border-radius:12px;padding:24px;margin:0 0 24px;border:1px solid #bbf7d0;">
                <table style="width:100%;border-collapse:collapse;">
                  <tr>
                    <td style="padding:8px 0;color:#64748b;font-size:14px;width:120px;">👤 Candidate</td>
                    <td style="padding:8px 0;color:#1e293b;font-size:14px;font-weight:600;">{candidate_name}</td>
                  </tr>
                  <tr>
                    <td style="padding:8px 0;color:#64748b;font-size:14px;">📧 Email</td>
                    <td style="padding:8px 0;color:#1e293b;font-size:14px;">{candidate_email}</td>
                  </tr>
                  <tr>
                    <td style="padding:8px 0;color:#64748b;font-size:14px;">📅 Date</td>
                    <td style="padding:8px 0;color:#1e293b;font-size:14px;font-weight:600;">{date_str}</td>
                  </tr>
                  <tr>
                    <td style="padding:8px 0;color:#64748b;font-size:14px;">🕐 Time</td>
                    <td style="padding:8px 0;color:#1e293b;font-size:14px;font-weight:600;">{time_str}</td>
                  </tr>
                </table>
              </div>
              <div style="text-align:center;">
                <a href="{meet_link}" style="display:inline-block;background:#059669;color:#fff;text-decoration:none;padding:12px 32px;border-radius:8px;font-size:14px;font-weight:600;">
                  Open Zoom Link
                </a>
              </div>
            </div>
          </div>
        </body>
        </html>
        """
        EmailService.send_email(recruiter_email, f"📋 New Interview: {candidate_name} — {role} | {date_str}", html)
