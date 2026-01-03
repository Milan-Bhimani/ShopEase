"""
==============================================================================
Email Service Module (email.py)
==============================================================================

PURPOSE:
--------
This module handles sending transactional emails for the e-commerce application.
It provides:
1. SMTP connection management (using Brevo/Sendinblue)
2. Generic email sending functionality
3. Pre-built email templates for orders (confirmation, cancellation)
4. HTML and plain text email support

WHY BREVO (SENDINBLUE)?
-----------------------
We chose Brevo for sending transactional emails because:

1. **Free Tier**: 300 emails/day free - sufficient for small to medium apps
2. **Reliability**: High deliverability rates and good reputation
3. **Easy SMTP**: Simple SMTP integration (no complex API needed)
4. **No Domain Verification Required**: Can start sending immediately
5. **Analytics**: Track opens, clicks, and bounces

Alternative options considered:
- SendGrid: More features but complex setup
- AWS SES: Cheapest at scale but requires domain verification
- Mailgun: Good API but no free tier

EMAIL TYPES IN THIS APP:
------------------------
1. OTP Verification - Sent during login (handled in auth/utils.py)
2. Order Confirmation - Sent when order is placed
3. Order Cancellation - Sent when order is cancelled

SMTP FLOW:
----------
    1. Connect to SMTP server (smtp-relay.brevo.com:587)
    2. Start TLS encryption
    3. Authenticate with Brevo credentials
    4. Send email message
    5. Close connection

HTML EMAIL DESIGN:
------------------
Emails use inline CSS because:
- Many email clients strip <style> tags
- Inline styles have best compatibility
- Gmail, Outlook, Yahoo all support inline CSS

We include plain text version as fallback for:
- Email clients that don't support HTML
- Accessibility (screen readers)
- Better spam score (multipart is trusted more)
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
    """
    Service for sending transactional emails.

    This class encapsulates all email sending logic, making it easy to:
    - Switch email providers (just change connection details)
    - Add new email types (add new template methods)
    - Test email functionality (mock this class)

    Usage:
        from app.email import email_service

        # Send order confirmation
        email_service.send_order_confirmation(
            to_email="customer@example.com",
            order=order_data,
            user_name="John"
        )
    """

    def __init__(self):
        """
        Initialize email service with settings.

        Settings are loaded from environment variables via config.py.
        """
        self.settings = get_settings()

    def _get_smtp_connection(self):
        """
        Create SMTP connection using Brevo credentials.

        This establishes a secure connection to Brevo's SMTP server:
        1. Connect to server on port 587 (TLS port)
        2. Start TLS encryption (upgrade plain connection to secure)
        3. Authenticate with Brevo credentials

        Returns:
            smtplib.SMTP: Authenticated SMTP connection

        Note:
            Connection should be closed after use with server.quit()
        """
        server = smtplib.SMTP(self.settings.SMTP_HOST, self.settings.SMTP_PORT)
        server.starttls()  # Upgrade to TLS encryption
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
        Send an email with HTML content (and optional plain text fallback).

        This is the core method used by all other email methods.
        It handles:
        - Email construction (headers, MIME types)
        - Connection management
        - Error handling and logging

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML body of the email
            text_content: Plain text fallback (optional, recommended)

        Returns:
            True if email was sent successfully, False otherwise

        Why return bool instead of raising?
            Email is often non-critical. We log errors but don't crash the app
            if email fails. The caller can decide whether to retry or ignore.
        """
        # Check if email is enabled (master switch)
        if not self.settings.EMAIL_ENABLED:
            # In development, just log what would have been sent
            logger.info(f"Email disabled. Would have sent to {to_email}: {subject}")
            return True  # Return True so the app flow continues

        try:
            # Create multipart message (contains both text and HTML versions)
            # 'alternative' means: show HTML if supported, otherwise text
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.settings.SMTP_FROM_NAME} <{self.settings.SMTP_FROM_EMAIL}>"
            msg['To'] = to_email

            # Add plain text part first (email clients read last part first,
            # so HTML should come after text to be preferred)
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)

            # Add HTML part (this is what most email clients will display)
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)

            # Send email via SMTP
            server = self._get_smtp_connection()
            server.sendmail(self.settings.SMTP_FROM_EMAIL, to_email, msg.as_string())
            server.quit()  # Close connection properly

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            # Log error but don't crash - email should not block user operations
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    # ==========================================================================
    # ORDER EMAIL METHODS
    # ==========================================================================

    def send_order_confirmation(
        self,
        to_email: str,
        order: Dict[str, Any],
        user_name: str
    ) -> bool:
        """
        Send order confirmation email after successful order placement.

        This email includes:
        - Order number and date
        - List of items with images
        - Price breakdown (subtotal, tax, shipping, total)
        - Shipping address
        - Estimated delivery date

        Args:
            to_email: Customer's email address
            order: Order document from database (contains items, totals, etc.)
            user_name: Customer's first name for personalization

        Returns:
            True if email sent successfully
        """
        subject = f"Order Confirmed - {order.get('order_number', 'N/A')}"

        # Generate both HTML and plain text versions
        html_content = self._get_order_confirmation_template(order, user_name)
        text_content = self._get_order_confirmation_text(order, user_name)

        return self.send_email(to_email, subject, html_content, text_content)

    def send_order_cancellation(
        self,
        to_email: str,
        order: Dict[str, Any],
        user_name: str
    ) -> bool:
        """
        Send order cancellation confirmation email.

        This email includes:
        - Order number that was cancelled
        - List of cancelled items
        - Refund information

        Args:
            to_email: Customer's email address
            order: Order document from database
            user_name: Customer's first name for personalization

        Returns:
            True if email sent successfully
        """
        subject = f"Order Cancelled - {order.get('order_number', 'N/A')}"

        html_content = self._get_order_cancellation_template(order, user_name)
        text_content = self._get_order_cancellation_text(order, user_name)

        return self.send_email(to_email, subject, html_content, text_content)

    # ==========================================================================
    # HELPER METHODS
    # ==========================================================================

    def _format_price(self, amount: float) -> str:
        """
        Format price in Indian Rupees (INR).

        Args:
            amount: Price as float

        Returns:
            Formatted string like "₹1,234.56"

        Note:
            Uses Indian numbering system would require custom formatting.
            Currently uses standard comma separation for simplicity.
        """
        return f"₹{amount:,.2f}"

    # ==========================================================================
    # EMAIL TEMPLATES
    # ==========================================================================
    # Templates use inline CSS for maximum email client compatibility.
    # Colors match the ShopEase brand (#2874f0 blue, #172337 dark footer).

    def _get_order_confirmation_template(self, order: Dict[str, Any], user_name: str) -> str:
        """
        Generate order confirmation HTML email template.

        The template includes:
        - ShopEase branded header with gradient background
        - Success checkmark icon
        - Order details table
        - Item list with images
        - Price breakdown
        - Shipping address
        - Track order button (CTA)
        - Dark footer with support info

        Args:
            order: Order data dictionary
            user_name: Customer's first name

        Returns:
            Complete HTML email as string
        """
        # Build items HTML - each item shows image, name, quantity, price
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

        # Build shipping address HTML
        shipping_address = order.get('shipping_address', {})
        address_html = f"""
            {shipping_address.get('full_name', '')}<br>
            {shipping_address.get('address_line1', '')}<br>
            {shipping_address.get('address_line2', '') + '<br>' if shipping_address.get('address_line2') else ''}
            {shipping_address.get('city', '')}, {shipping_address.get('state', '')} - {shipping_address.get('pincode', '')}<br>
            Phone: {shipping_address.get('phone', '')}
        """

        # Complete HTML template with all sections
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <!-- Header with gradient background (ShopEase blue) -->
            <div style="background: linear-gradient(135deg, #2874f0 0%, #1a5dc8 100%); padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">🛍️ ShopEase</h1>
            </div>

            <!-- Main Content -->
            <div style="background: #fff; padding: 30px; border: 1px solid #e0e0e0; border-top: none;">
                <!-- Success Icon (green checkmark circle) -->
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="width: 80px; height: 80px; background: #e8f5e9; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;">
                        <span style="font-size: 40px;">✓</span>
                    </div>
                </div>

                <h2 style="color: #388e3c; text-align: center; margin-bottom: 10px;">Order Confirmed!</h2>
                <p style="text-align: center; color: #666; margin-bottom: 30px;">
                    Hi {user_name}, thank you for your order!
                </p>

                <!-- Order Details Box -->
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

                <!-- Order Items Section -->
                <h3 style="border-bottom: 2px solid #2874f0; padding-bottom: 10px;">Order Items</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    {items_html}
                </table>

                <!-- Price Summary Box -->
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

                <!-- Shipping Address Section -->
                <h3 style="border-bottom: 2px solid #2874f0; padding-bottom: 10px; margin-top: 30px;">Shipping Address</h3>
                <div style="background: #f9f9f9; padding: 15px; border-radius: 8px;">
                    {address_html}
                </div>

                <!-- Call to Action Button -->
                <div style="text-align: center; margin-top: 30px;">
                    <a href="#" style="background: #2874f0; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; display: inline-block;">
                        Track Your Order
                    </a>
                </div>
            </div>

            <!-- Dark Footer -->
            <div style="background: #172337; color: #878787; padding: 20px; text-align: center; border-radius: 0 0 8px 8px;">
                <p style="margin: 0 0 10px;">Need help? Contact us at support@shopease.com</p>
                <p style="margin: 0; font-size: 12px;">© 2024 ShopEase. All rights reserved.</p>
            </div>
        </body>
        </html>
        """

    def _get_order_confirmation_text(self, order: Dict[str, Any], user_name: str) -> str:
        """
        Generate plain text version of order confirmation.

        This is used as fallback when HTML is not supported.
        Formatting uses simple text alignment and separators.

        Args:
            order: Order data dictionary
            user_name: Customer's first name

        Returns:
            Plain text email content
        """
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
        """
        Generate order cancellation HTML email template.

        Similar structure to confirmation but with:
        - Red color scheme for cancellation
        - X icon instead of checkmark
        - Refund information section

        Args:
            order: Order data dictionary
            user_name: Customer's first name

        Returns:
            Complete HTML email as string
        """
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
                <!-- Cancel Icon (red X circle) -->
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

                <!-- Cancelled Items (red border instead of blue) -->
                <h3 style="border-bottom: 2px solid #d32f2f; padding-bottom: 10px;">Cancelled Items</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    {items_html}
                </table>

                <!-- Refund Information Box (blue info style) -->
                <div style="background: #e3f2fd; padding: 20px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #2874f0;">
                    <h4 style="margin: 0 0 10px; color: #1565c0;">💰 Refund Information</h4>
                    <p style="margin: 0; color: #666;">
                        If you paid online, your refund of <strong>{self._format_price(order.get('total', 0))}</strong> will be processed within 5-7 business days.
                    </p>
                </div>

                <!-- Continue Shopping CTA -->
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
        """
        Generate plain text version of order cancellation.

        Args:
            order: Order data dictionary
            user_name: Customer's first name

        Returns:
            Plain text email content
        """
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


# ==============================================================================
# SINGLETON INSTANCE
# ==============================================================================
# Create single instance for use throughout the application.
# Import this instance: from app.email import email_service
email_service = EmailService()
