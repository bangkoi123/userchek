from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, Content
import os
from datetime import datetime
from typing import Optional, Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailDeliveryError(Exception):
    pass

class EmailService:
    def __init__(self):
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.sender_email = os.getenv('SENDER_EMAIL', 'noreply@webtools-validation.com')
        
        if not self.api_key or self.api_key == 'your-sendgrid-api-key-here':
            logger.warning("SendGrid API key not configured. Email notifications will be simulated.")
            self.mock_mode = True
        else:
            self.mock_mode = False
            self.sg = SendGridAPIClient(self.api_key)

    def send_email(self, to_email: str, subject: str, html_content: str, plain_content: str = None) -> bool:
        """Send email using SendGrid or simulate in mock mode"""
        
        if self.mock_mode:
            logger.info(f"📧 [MOCK] Email sent to {to_email}: {subject}")
            return True
            
        try:
            message = Mail(
                from_email=From(self.sender_email, "Webtools Validation"),
                to_emails=To(to_email),
                subject=Subject(subject),
                html_content=Content("text/html", html_content)
            )
            
            if plain_content:
                message.content = [
                    Content("text/plain", plain_content),
                    Content("text/html", html_content)
                ]
            
            response = self.sg.send(message)
            logger.info(f"📧 Email sent to {to_email}: {subject} (Status: {response.status_code})")
            return response.status_code == 202
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
            raise EmailDeliveryError(f"Failed to send email: {str(e)}")

    def send_welcome_email(self, user_email: str, username: str, credits: int = 1000) -> bool:
        """Send welcome email for new users"""
        subject = "🎉 Selamat datang di Webtools Validasi Nomor Telepon!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Welcome to Webtools</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(90deg, #3b82f6, #2563eb); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;">
                <h1 style="color: white; margin: 0; font-size: 28px;">🚀 Selamat Datang!</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">Webtools Validasi Nomor Telepon</p>
            </div>
            
            <div style="background: #f8fafc; padding: 25px; border-radius: 10px; margin-bottom: 25px;">
                <h2 style="color: #1e40af; margin-top: 0;">Halo {username}! 👋</h2>
                <p style="color: #374151; line-height: 1.6;">
                    Terima kasih telah bergabung dengan <strong>Webtools Validasi Nomor Telepon</strong>! 
                    Kami senang Anda menjadi bagian dari platform validasi nomor terdepan.
                </p>
            </div>

            <div style="background: #ecfdf5; border: 1px solid #a7f3d0; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
                <h3 style="color: #065f46; margin-top: 0;">🎁 Kredit Gratis</h3>
                <p style="color: #047857; margin: 0;">
                    Akun Anda telah dikreditkan dengan <strong>{credits:,} kredit gratis</strong> untuk memulai validasi nomor telepon!
                </p>
            </div>

            <h3 style="color: #1e40af;">🚀 Apa yang bisa Anda lakukan:</h3>
            <ul style="color: #374151; line-height: 1.8;">
                <li><strong>Quick Check</strong> - Validasi satu nomor telepon secara instan</li>
                <li><strong>Bulk Check</strong> - Upload file CSV/Excel untuk validasi massal</li>
                <li><strong>Job History</strong> - Pantau riwayat semua pekerjaan validasi</li>
                <li><strong>Dashboard</strong> - Lihat statistik penggunaan dan kredit</li>
            </ul>

            <div style="text-align: center; margin: 30px 0;">
                <a href="https://phonehub-6.preview.emergentagent.com" 
                   style="background: #3b82f6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                    🎯 Mulai Validasi Sekarang
                </a>
            </div>

            <div style="background: #f1f5f9; padding: 20px; border-radius: 10px; margin-top: 30px;">
                <h4 style="color: #475569; margin-top: 0;">💡 Tips untuk Memulai:</h4>
                <ol style="color: #64748b; line-height: 1.6;">
                    <li>Login ke dashboard dengan kredensial Anda</li>
                    <li>Coba fitur Quick Check dengan nomor telepon</li>
                    <li>Download sample CSV untuk testing Bulk Check</li>
                    <li>Pantau penggunaan kredit di dashboard</li>
                </ol>
            </div>

            <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                <p style="color: #64748b; font-size: 14px; margin: 0;">
                    Butuh bantuan? Hubungi support kami atau baca dokumentasi lengkap.
                </p>
                <p style="color: #64748b; font-size: 12px; margin: 10px 0 0 0;">
                    © 2025 Webtools Validasi. Semua hak dilindungi.
                </p>
            </div>
        </body>
        </html>
        """
        
        plain_content = f"""
        Selamat datang di Webtools Validasi Nomor Telepon!
        
        Halo {username}!
        
        Terima kasih telah bergabung dengan Webtools Validasi Nomor Telepon!
        
        Kredit Gratis: {credits:,} kredit telah dikreditkan ke akun Anda.
        
        Fitur yang tersedia:
        - Quick Check: Validasi satu nomor telepon secara instan
        - Bulk Check: Upload file CSV/Excel untuk validasi massal
        - Job History: Pantau riwayat semua pekerjaan validasi
        - Dashboard: Lihat statistik penggunaan dan kredit
        
        Mulai sekarang: https://phonehub-6.preview.emergentagent.com
        
        Tips untuk memulai:
        1. Login ke dashboard dengan kredensial Anda
        2. Coba fitur Quick Check dengan nomor telepon
        3. Download sample CSV untuk testing Bulk Check
        4. Pantau penggunaan kredit di dashboard
        
        © 2025 Webtools Validasi
        """
        
        return self.send_email(user_email, subject, html_content, plain_content)

    def send_job_completion_email(self, user_email: str, username: str, job_data: Dict[str, Any]) -> bool:
        """Send email notification when bulk validation job is completed"""
        
        job_id = job_data.get('_id', 'Unknown')
        filename = job_data.get('filename', 'Unknown')
        total_numbers = job_data.get('total_numbers', 0)
        results = job_data.get('results', {})
        
        whatsapp_active = results.get('whatsapp_active', 0)
        telegram_active = results.get('telegram_active', 0)
        inactive = results.get('inactive', 0)
        errors = results.get('errors', 0)
        
        subject = f"✅ Bulk Validation Selesai: {filename}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(90deg, #10b981, #059669); padding: 25px; border-radius: 10px; text-align: center; margin-bottom: 25px;">
                <h1 style="color: white; margin: 0; font-size: 24px;">✅ Validasi Selesai!</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0;">Job ID: {job_id[:8]}...</p>
            </div>
            
            <h2 style="color: #065f46;">Halo {username}!</h2>
            <p style="color: #374151; line-height: 1.6;">
                Bulk validation untuk file <strong>"{filename}"</strong> telah berhasil diselesaikan! 
                Berikut adalah ringkasan hasil validasi:
            </p>

            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h3 style="color: #065f46; margin-top: 0;">📊 Hasil Validasi</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #d1fae5;">
                        <td style="padding: 8px 0; color: #047857;"><strong>Total Numbers:</strong></td>
                        <td style="padding: 8px 0; text-align: right; color: #065f46; font-weight: bold;">{total_numbers:,}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #d1fae5;">
                        <td style="padding: 8px 0; color: #047857;">WhatsApp Active:</td>
                        <td style="padding: 8px 0; text-align: right; color: #059669; font-weight: bold;">{whatsapp_active:,}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #d1fae5;">
                        <td style="padding: 8px 0; color: #047857;">Telegram Active:</td>
                        <td style="padding: 8px 0; text-align: right; color: #0ea5e9; font-weight: bold;">{telegram_active:,}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #d1fae5;">
                        <td style="padding: 8px 0; color: #047857;">Inactive:</td>
                        <td style="padding: 8px 0; text-align: right; color: #dc2626; font-weight: bold;">{inactive:,}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; color: #047857;">Errors:</td>
                        <td style="padding: 8px 0; text-align: right; color: #f59e0b; font-weight: bold;">{errors:,}</td>
                    </tr>
                </table>
            </div>

            <div style="text-align: center; margin: 25px 0;">
                <a href="https://phonehub-6.preview.emergentagent.com/job-history" 
                   style="background: #10b981; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                    📥 Download Hasil
                </a>
            </div>

            <div style="background: #eff6ff; border: 1px solid #bfdbfe; padding: 15px; border-radius: 8px; margin-top: 25px;">
                <p style="color: #1e40af; margin: 0; font-size: 14px;">
                    💡 <strong>Tip:</strong> Hasil validasi dapat diunduh dalam format CSV dari halaman Job History. 
                    Hasil akan tersimpan selama 30 hari.
                </p>
            </div>

            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                <p style="color: #64748b; font-size: 14px; margin: 0;">
                    Terima kasih menggunakan Webtools Validasi!
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_content)

    def send_low_credit_alert(self, user_email: str, username: str, current_credits: int, threshold: int = 100) -> bool:
        """Send email alert when user credits are running low"""
        
        subject = f"⚠️ Kredit Hampir Habis - {current_credits} kredit tersisa"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(90deg, #f59e0b, #d97706); padding: 25px; border-radius: 10px; text-align: center; margin-bottom: 25px;">
                <h1 style="color: white; margin: 0; font-size: 24px;">⚠️ Kredit Hampir Habis</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0;">Webtools Validasi</p>
            </div>
            
            <h2 style="color: #92400e;">Halo {username}!</h2>
            <p style="color: #374151; line-height: 1.6;">
                Kredit akun Anda hampir habis. Saat ini Anda memiliki <strong>{current_credits} kredit</strong> tersisa.
            </p>

            <div style="background: #fef3c7; border: 1px solid #fcd34d; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h3 style="color: #92400e; margin-top: 0;">💡 Informasi Penting</h3>
                <ul style="color: #d97706; margin: 0; padding-left: 20px;">
                    <li>Setiap validasi membutuhkan 2 kredit</li>
                    <li>Estimasi validasi tersisa: <strong>{current_credits // 2} nomor</strong></li>
                    <li>Kredit habis = tidak bisa melakukan validasi</li>
                </ul>
            </div>

            <div style="text-align: center; margin: 25px 0;">
                <a href="https://phonehub-6.preview.emergentagent.com" 
                   style="background: #f59e0b; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin-right: 10px;">
                    💳 Beli Kredit
                </a>
                <a href="https://phonehub-6.preview.emergentagent.com/dashboard" 
                   style="background: #6b7280; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                    📊 Lihat Dashboard
                </a>
            </div>

            <div style="background: #f1f5f9; padding: 15px; border-radius: 8px; margin-top: 25px;">
                <h4 style="color: #475569; margin-top: 0;">📈 Paket Kredit Tersedia:</h4>
                <ul style="color: #64748b; margin: 0; padding-left: 20px;">
                    <li><strong>Starter:</strong> 1,000 kredit - Perfect untuk testing</li>
                    <li><strong>Professional:</strong> 5,000 kredit - Untuk kebutuhan regular</li>
                    <li><strong>Enterprise:</strong> 25,000 kredit - Untuk volume tinggi</li>
                </ul>
            </div>

            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                <p style="color: #64748b; font-size: 14px; margin: 0;">
                    Questions? Contact our support team anytime.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_content)

# Create global email service instance
email_service = EmailService()