
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from config import EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_test_email():
    """Send a test email to confirm the bot is active"""
    subject = "Sports Arbitrage Bot - Active"
    body = """
    <html>
    <body>
        <h2>Sports Arbitrage Bot is now active</h2>
        <p>This is a confirmation that your sports arbitrage bot is now running and actively monitoring betting sites.</p>
        <p>You will receive notifications only when arbitrage opportunities are found or if the bot requires attention.</p>
        <hr>
        <p><i>This is an automated message. Please do not reply.</i></p>
    </body>
    </html>
    """
    
    return send_email(subject, body)

def send_opportunity_email(opportunity_data):
    """Send an email with the arbitrage opportunity details"""
    subject = f"Arbitrage Opportunity Found - {opportunity_data['profit_percentage']:.2f}% Profit"
    
    body = f"""
    <html>
    <body>
        <h2>Arbitrage Opportunity Detected</h2>
        <p><b>Potential Profit:</b> {opportunity_data['profit_percentage']:.2f}%</p>
        <p><b>Event:</b> {opportunity_data['event']}</p>
        <p><b>Sport:</b> {opportunity_data['sport']}</p>
        <p><b>Date/Time:</b> {opportunity_data['datetime']}</p>
        
        <h3>Betting Details:</h3>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">
            <tr>
                <th>Bookmaker</th>
                <th>Selection</th>
                <th>Odds</th>
                <th>Stake %</th>
                <th>Stake Amount*</th>
            </tr>
    """
    
    for bet in opportunity_data['bets']:
        body += f"""
            <tr>
                <td>{bet['bookmaker']}</td>
                <td>{bet['selection']}</td>
                <td>{bet['odds']}</td>
                <td>{bet['stake_percentage']:.2f}%</td>
                <td>${bet['stake_amount']:.2f}</td>
            </tr>
        """
    
    body += f"""
        </table>
        <p><small>* Based on a total stake of ${opportunity_data['total_stake']:.2f}</small></p>
        
        <h3>Details:</h3>
        <ul>
            <li><b>Bet Type:</b> {opportunity_data['bet_type']}</li>
            <li><b>Market:</b> {opportunity_data['market']}</li>
            <li><b>Expected Return:</b> ${opportunity_data['expected_return']:.2f}</li>
        </ul>
        
        <p style="color: red;"><b>Note:</b> Odds may change quickly. Please verify all information before placing bets.</p>
        <hr>
        <p><i>This is an automated message from your Sports Arbitrage Bot.</i></p>
    </body>
    </html>
    """
    
    return send_email(subject, body)

def send_error_email(error_message):
    """Send an email to notify about errors"""
    subject = "Sports Arbitrage Bot - Error Alert"
    body = f"""
    <html>
    <body>
        <h2>Error Detected in Sports Arbitrage Bot</h2>
        <p>The following error has occurred:</p>
        <div style="background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px;">
            <pre>{error_message}</pre>
        </div>
        <p>Please check the bot configuration and operation.</p>
        <hr>
        <p><i>This is an automated message. Please address this issue as soon as possible.</i></p>
    </body>
    </html>
    """
    
    return send_email(subject, body)

def send_email(subject, body_html):
    """Generic function to send emails"""
    try:
        message = MIMEMultipart()
        message['From'] = EMAIL_SENDER
        message['To'] = EMAIL_RECEIVER
        message['Subject'] = subject
        
        message.attach(MIMEText(body_html, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        text = message.as_string()
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, text)
        server.quit()
        
        logger.info(f"Email sent successfully: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False
