"""
Email service for sending transactional emails.
Uses Brevo (Sendinblue) SMTP for email delivery.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime

from .config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending transactional emails."""

    def __init__(self):
        self.settings = get_settings()

    def _get_smtp_connection(self):
        """Create SMTP connection using Brevo credentials."""
        server = smtplib.SMTP(self.settings.SMTP_HOST, self.settings.SMTP_PORT)
        server.starttls()
        server.login(self.settings.BREVO_SMTP_LOGIN, self.settings.BREVO_SMTP_PASSWORD)
        return server

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body of the email
            text_content: Plain text fallback (optional)

        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.settings.EMAIL_ENABLED:
            logger.info(f"Email disabled. Would have sent to {to_email}: {subject}")
            return True

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.settings.SMTP_FROM_NAME} <{self.settings.SMTP_FROM_EMAIL}>"
            msg['To'] = to_email

            # Add plain text part
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)

            # Add HTML part
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)

            # Send email
            server = self._get_smtp_connection()
            server.sendmail(self.settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
            server.quit()

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_order_confirmation(
        self,
        to_email: str,
        order: Dict[str, Any],
        user_name: str
    ) -> bool:
        """Send order confirmation email."""
        subject = f"Order Confirmed - {order.get('order_number', 'N/A')}"

        html_content = self._get_order_confirmation_template(order, user_name)
        text_content = self._get_order_confirmation_text(order, user_name)

        return self.send_email(to_email, subject, html_content, text_content)

    def send_order_cancellation(
        self,
        to_email: str,
        order: Dict[str, Any],
        user_name: str
    ) -> bool:
        """Send order cancellation email."""
        subject = f"Order Cancelled - {order.get('order_number', 'N/A')}"

        html_content = self._get_order_cancellation_template(order, user_name)
        text_content = self._get_order_cancellation_text(order, user_name)

        return self.send_email(to_email, subject, html_content, text_content)

    def _format_price(self, amount: float) -> str:
        """Format price in INR."""
        return f"₹{amount:,.2f}"

    def _get_order_confirmation_template(self, order: Dict[str, Any], user_name: str) -> str:
        """Generate order confirmation HTML email template."""
        items_html = ""
        for item in order.get('items', []):
            items_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">
                    <div style="display: flex; align-items: center;">
                        <img src="{item.get('product_image', '')}" alt="{item.get('product_name', '')}"
                             style="width: 60px; height: 60px; object-fit: contain; margin-right: 12px; border-radius: 4px;">
                        <div>
                            <strong>{item.get('product_name', 'Product')}</strong><br>
                            <small style="color: #666;">Qty: {item.get('quantity', 1)}</small>
                        </div>
                    </div>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right;">
                    {self._format_price(item.get('subtotal', 0))}
                </td>
            </tr>
            """

        shipping_address = order.get('shipping_address', {})
        address_html = f"""
            {shipping_address.get('full_name', '')}<br>
            {shipping_address.get('address_line1', '')}<br>
            {shipping_address.get('address_line2', '') + '<br>' if shipping_address.get('address_line2') else ''}
            {shipping_address.get('city', '')}, {shipping_address.get('state', '')} - {shipping_address.get('pincode', '')}<br>
            Phone: {shipping_address.get('phone', '')}
        """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #2874f0 0%, #1a5dc8 100%); padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">🛍️ ShopEase</h1>
            </div>

            <!-- Content -->
            <div style="background: #fff; padding: 30px; border: 1px solid #e0e0e0; border-top: none;">
                <!-- Success Icon -->
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="width: 80px; height: 80px; background: #e8f5e9; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;">
                        <span style="font-size: 40px;">✓</span>
                    </div>
                </div>

                <h2 style="color: #388e3c; text-align: center; margin-bottom: 10px;">Order Confirmed!</h2>
                <p style="text-align: center; color: #666; margin-bottom: 30px;">
                    Hi {user_name}, thank you for your order!
                </p>

                <!-- Order Details -->
                <div style="background: #f9f9f9; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0;"><strong>Order Number:</strong></td>
                            <td style="padding: 8px 0; text-align: right; color: #2874f0; font-weight: bold;">{order.get('order_number', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;"><strong>Order Date:</strong></td>
                            <td style="padding: 8px 0; text-align: right;">{datetime.now().strftime('%B %d, %Y')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;"><strong>Payment Method:</strong></td>
                            <td style="padding: 8px 0; text-align: right;">{order.get('payment_method', 'N/A').upper()}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;"><strong>Estimated Delivery:</strong></td>
                            <td style="padding: 8px 0; text-align: right; color: #388e3c;">{order.get('estimated_delivery', 'N/A')}</td>
                        </tr>
                    </table>
                </div>

                <!-- Items -->
                <h3 style="border-bottom: 2px solid #2874f0; padding-bottom: 10px;">Order Items</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    {items_html}
                </table>

                <!-- Price Summary -->
                <div style="background: #f9f9f9; padding: 20px; border-radius: 8px; margin-top: 20px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0;">Subtotal:</td>
                            <td style="padding: 8px 0; text-align: right;">{self._format_price(order.get('subtotal', 0))}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;">Tax (18% GST):</td>
                            <td style="padding: 8px 0; text-align: right;">{self._format_price(order.get('tax', 0))}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;">Shipping:</td>
                            <td style="padding: 8px 0; text-align: right;">{self._format_price(order.get('shipping_cost', 0)) if order.get('shipping_cost', 0) > 0 else '<span style="color: #388e3c;">FREE</span>'}</td>
                        </tr>
                        <tr style="border-top: 2px solid #ddd;">
                            <td style="padding: 12px 0; font-size: 18px;"><strong>Total:</strong></td>
                            <td style="padding: 12px 0; text-align: right; font-size: 18px; color: #2874f0;"><strong>{self._format_price(order.get('total', 0))}</strong></td>
                        </tr>
                    </table>
                </div>

                <!-- Shipping Address -->
                <h3 style="border-bottom: 2px solid #2874f0; padding-bottom: 10px; margin-top: 30px;">Shipping Address</h3>
                <div style="background: #f9f9f9; padding: 15px; border-radius: 8px;">
                    {address_html}
                </div>

                <!-- CTA Button -->
                <div style="text-align: center; margin-top: 30px;">
                    <a href="#" style="background: #2874f0; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; display: inline-block;">
                        Track Your Order
                    </a>
                </div>
            </div>

            <!-- Footer -->
            <div style="background: #172337; color: #878787; padding: 20px; text-align: center; border-radius: 0 0 8px 8px;">
                <p style="margin: 0 0 10px;">Need help? Contact us at support@shopease.com</p>
                <p style="margin: 0; font-size: 12px;">© 2024 ShopEase. All rights reserved.</p>
            </div>
        </body>
        </html>
        """

    def _get_order_confirmation_text(self, order: Dict[str, Any], user_name: str) -> str:
        """Generate plain text version of order confirmation."""
        items_text = "\n".join([
            f"  - {item.get('product_name', 'Product')} x {item.get('quantity', 1)} = {self._format_price(item.get('subtotal', 0))}"
            for item in order.get('items', [])
        ])

        return f"""
ORDER CONFIRMED - ShopEase

Hi {user_name},

Thank you for your order! Your order has been confirmed.

ORDER DETAILS
-------------
Order Number: {order.get('order_number', 'N/A')}
Order Date: {datetime.now().strftime('%B %d, %Y')}
Payment Method: {order.get('payment_method', 'N/A').upper()}
Estimated Delivery: {order.get('estimated_delivery', 'N/A')}

ITEMS
-----
{items_text}

SUMMARY
-------
Subtotal: {self._format_price(order.get('subtotal', 0))}
Tax (18% GST): {self._format_price(order.get('tax', 0))}
Shipping: {self._format_price(order.get('shipping_cost', 0)) if order.get('shipping_cost', 0) > 0 else 'FREE'}
Total: {self._format_price(order.get('total', 0))}

Need help? Contact us at support@shopease.com

© 2024 ShopEase. All rights reserved.
        """

    def _get_order_cancellation_template(self, order: Dict[str, Any], user_name: str) -> str:
        """Generate order cancellation HTML email template."""
        items_html = ""
        for item in order.get('items', []):
            items_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">
                    {item.get('product_name', 'Product')} x {item.get('quantity', 1)}
                </td>
                <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right;">
                    {self._format_price(item.get('subtotal', 0))}
                </td>
            </tr>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #2874f0 0%, #1a5dc8 100%); padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">🛍️ ShopEase</h1>
            </div>

            <!-- Content -->
            <div style="background: #fff; padding: 30px; border: 1px solid #e0e0e0; border-top: none;">
                <!-- Cancel Icon -->
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="width: 80px; height: 80px; background: #ffebee; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;">
                        <span style="font-size: 40px;">✕</span>
                    </div>
                </div>

                <h2 style="color: #d32f2f; text-align: center; margin-bottom: 10px;">Order Cancelled</h2>
                <p style="text-align: center; color: #666; margin-bottom: 30px;">
                    Hi {user_name}, your order has been successfully cancelled.
                </p>

                <!-- Order Details -->
                <div style="background: #f9f9f9; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0;"><strong>Order Number:</strong></td>
                            <td style="padding: 8px 0; text-align: right; color: #d32f2f; font-weight: bold;">{order.get('order_number', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0;"><strong>Cancellation Date:</strong></td>
                            <td style="padding: 8px 0; text-align: right;">{datetime.now().strftime('%B %d, %Y')}</td>
                        </tr>
                    </table>
                </div>

                <!-- Items -->
                <h3 style="border-bottom: 2px solid #d32f2f; padding-bottom: 10px;">Cancelled Items</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    {items_html}
                </table>

                <!-- Refund Info -->
                <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #2874f0;">
                    <h4 style="margin: 0 0 10px; color: #1565c0;">💰 Refund Information</h4>
                    <p style="margin: 0; color: #666;">
                        If you paid online, your refund of <strong>{self._format_price(order.get('total', 0))}</strong> will be processed within 5-7 business days.
                    </p>
                </div>

                <!-- CTA Button -->
                <div style="text-align: center; margin-top: 30px;">
                    <a href="#" style="background: #2874f0; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; display: inline-block;">
                        Continue Shopping
                    </a>
                </div>
            </div>

            <!-- Footer -->
            <div style="background: #172337; color: #878787; padding: 20px; text-align: center; border-radius: 0 0 8px 8px;">
                <p style="margin: 0 0 10px;">Need help? Contact us at support@shopease.com</p>
                <p style="margin: 0; font-size: 12px;">© 2024 ShopEase. All rights reserved.</p>
            </div>
        </body>
        </html>
        """

    def _get_order_cancellation_text(self, order: Dict[str, Any], user_name: str) -> str:
        """Generate plain text version of order cancellation."""
        items_text = "\n".join([
            f"  - {item.get('product_name', 'Product')} x {item.get('quantity', 1)} = {self._format_price(item.get('subtotal', 0))}"
            for item in order.get('items', [])
        ])

        return f"""
ORDER CANCELLED - ShopEase

Hi {user_name},

Your order has been successfully cancelled.

ORDER DETAILS
-------------
Order Number: {order.get('order_number', 'N/A')}
Cancellation Date: {datetime.now().strftime('%B %d, %Y')}

CANCELLED ITEMS
---------------
{items_text}

REFUND INFORMATION
------------------
If you paid online, your refund of {self._format_price(order.get('total', 0))} will be processed within 5-7 business days.

Need help? Contact us at support@shopease.com

© 2024 ShopEase. All rights reserved.
        """


# Singleton instance
email_service = EmailService()
