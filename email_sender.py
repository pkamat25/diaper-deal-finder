import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import re

from dotenv import load_dotenv

load_dotenv()

def parse_markdown_to_html(content):
    """Convert markdown content to properly formatted HTML"""
    
    lines = content.split('\n')
    html_parts = []
    
    # Add header
    html_parts.append(f"""
    <div style="background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 8px; margin-bottom: 20px;">
        <h1 style="margin: 0; font-size: 24px;">🍼 Daily Diaper Deals</h1>
        <p style="margin: 5px 0 0 0; font-size: 16px;">Australian Supermarket Report</p>
        <p style="margin: 5px 0 0 0; font-size: 14px;">{datetime.now().strftime('%A, %d %B %Y')}</p>
    </div>
    """)
    
    # Process content
    table_started = False
    table_rows = []
    
    for line in lines:
        line = line.strip()
        
        # Handle table rows
        if line.startswith('|') and line.endswith('|'):
            if not table_started:
                table_started = True
                table_rows = []
            
            # Clean up the row
            cells = [cell.strip() for cell in line.split('|')[1:-1]]  # Remove empty first/last
            if cells and not all(cell == '' or set(cell) <= {'-', ' '} for cell in cells):  # Skip separator rows
                table_rows.append(cells)
        
        # End of table or non-table content
        else:
            if table_started and table_rows:
                # Create HTML table
                html_parts.append('<div style="margin: 20px 0;">')
                html_parts.append('''
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                ''')
                
                # Table header
                if table_rows:
                    html_parts.append('<thead>')
                    html_parts.append('<tr style="background-color: #4CAF50; color: white;">')
                    for header in table_rows[0]:
                        html_parts.append(f'<th style="padding: 12px; text-align: left; border: 1px solid #ddd;">{header}</th>')
                    html_parts.append('</tr>')
                    html_parts.append('</thead>')
                    
                    # Table body
                    html_parts.append('<tbody>')
                    for i, row in enumerate(table_rows[1:], 1):
                        bg_color = "#f2f2f2" if i % 2 == 0 else "white"
                        html_parts.append(f'<tr style="background-color: {bg_color};">')
                        for cell in row:
                            # Highlight special prices and savings
                            if '$' in cell and ('Save' in cell or '(' in cell):
                                cell_style = 'padding: 12px; border: 1px solid #ddd; font-weight: bold; color: #e74c3c;'
                            elif '$' in cell:
                                cell_style = 'padding: 12px; border: 1px solid #ddd; font-weight: bold; color: #27ae60;'
                            else:
                                cell_style = 'padding: 12px; border: 1px solid #ddd;'
                            html_parts.append(f'<td style="{cell_style}">{cell}</td>')
                        html_parts.append('</tr>')
                    html_parts.append('</tbody>')
                
                html_parts.append('</table>')
                html_parts.append('</div>')
                
                table_started = False
                table_rows = []
            
            # Handle non-table content
            if line:
                if line.startswith('**') and line.endswith('**'):
                    # Bold text (best deals)
                    text = line[2:-2]
                    html_parts.append(f'''
                    <div style="background-color: #fff3cd; border: 2px solid #ffc107; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="margin: 0 0 10px 0; color: #856404;">🏆 {text}</h3>
                    </div>
                    ''')
                elif line.startswith('#'):
                    # Headers
                    level = len(line) - len(line.lstrip('#'))
                    header_text = line.lstrip('# ')
                    html_parts.append(f'<h{level} style="color: #2c5530; margin: 20px 0 10px 0;">{header_text}</h{level}>')
                else:
                    # Regular text
                    html_parts.append(f'<p style="margin: 10px 0; line-height: 1.6;">{line}</p>')
    
    # Handle remaining table if content ends with table
    if table_started and table_rows:
        html_parts.append('<div style="margin: 20px 0;">')
        html_parts.append('''
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
        ''')
        
        if table_rows:
            html_parts.append('<thead>')
            html_parts.append('<tr style="background-color: #4CAF50; color: white;">')
            for header in table_rows[0]:
                html_parts.append(f'<th style="padding: 12px; text-align: left; border: 1px solid #ddd;">{header}</th>')
            html_parts.append('</tr>')
            html_parts.append('</thead>')
            
            html_parts.append('<tbody>')
            for i, row in enumerate(table_rows[1:], 1):
                bg_color = "#f2f2f2" if i % 2 == 0 else "white"
                html_parts.append(f'<tr style="background-color: {bg_color};">')
                for cell in row:
                    if '$' in cell and ('Save' in cell or '(' in cell):
                        cell_style = 'padding: 12px; border: 1px solid #ddd; font-weight: bold; color: #e74c3c;'
                    elif '$' in cell:
                        cell_style = 'padding: 12px; border: 1px solid #ddd; font-weight: bold; color: #27ae60;'
                    else:
                        cell_style = 'padding: 12px; border: 1px solid #ddd;'
                    html_parts.append(f'<td style="{cell_style}">{cell}</td>')
                html_parts.append('</tr>')
            html_parts.append('</tbody>')
        
        html_parts.append('</table>')
        html_parts.append('</div>')
    
    return '\n'.join(html_parts)

def send_diaper_deals():
    # YOUR EMAIL SETTINGS - CHANGE THESE
    
    sender_email = os.getenv('GMAIL_EMAIL')
    sender_password = os.getenv('GMAIL_PASSWORD') 
    recipient_email = os.getenv('RECIPIENT_EMAIL') #
    
    try:
        # Read the deals file
        file_name = "diaper_everyday_deals.md"
        
        if os.path.exists(file_name):
            with open(file_name, "r", encoding="utf-8") as file:
                deals_content = file.read()
            print("✅ Deals file found and read successfully")
            print(f"📄 Content preview: {deals_content[:100]}...")
        else:
            deals_content = """
# No Deals Found

No deals file was found. Please run your AutoGen script first to generate the deals.

**Next Steps:**
1. Run your AutoGen diaper deal search
2. Check that the file saves to the correct location
3. Try again with email notification
            """
            print("❌ Deals file not found - sending placeholder")
        
        # Create email
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"🍼 Daily Diaper Deals - {datetime.now().strftime('%d %B %Y')}"
        
        # Create plain text version (simple backup)
        plain_text = f"""
🍼 DAILY DIAPER DEALS REPORT
{datetime.now().strftime('%A, %d %B %Y')}

{deals_content}

---
Your automated diaper deal finder
Australian Supermarkets: Coles & Woolworths
Generated: {datetime.now().strftime('%I:%M %p')}
        """
        
        # Create beautifully formatted HTML version
        html_content = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    border-radius: 12px;
                    padding: 0;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .content {{
                    padding: 30px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    border-radius: 8px;
                    overflow: hidden;
                }}
                th {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 15px 12px;
                    text-align: left;
                    font-weight: 600;
                    font-size: 14px;
                }}
                td {{
                    padding: 12px;
                    border-bottom: 1px solid #eee;
                    font-size: 14px;
                }}
                tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                tr:hover {{
                    background-color: #e8f5e8;
                    transition: background-color 0.2s;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px 30px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                    border-top: 1px solid #eee;
                }}
                @media (max-width: 600px) {{
                    body {{ padding: 10px; }}
                    .content {{ padding: 20px; }}
                    th, td {{ padding: 8px 6px; font-size: 12px; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="content">
                    {parse_markdown_to_html(deals_content)}
                </div>
                <div class="footer">
                    <p><strong>🤖 Automated Report</strong> | Your Personal Diaper Deal Finder</p>
                    <p>Monitoring: Coles & Woolworths Australia | Generated: {datetime.now().strftime('%I:%M %p')}</p>
                    <p>Next scan: Tomorrow at 9:00 AM | Made with ❤️ for smart parents</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attach both versions
        text_part = MIMEText(plain_text, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        print("📧 Sending beautifully formatted email...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        print("✅ Email sent successfully with proper table formatting!")
        print("📱 Check your email - tables should now display perfectly!")
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False

# Test function
def test_email():
    print("🧪 Testing improved email formatting...")
    success = send_diaper_deals()
    if success:
        print("🎉 Email formatting test completed!")
        print("📧 Check your inbox for the properly formatted table")
    else:
        print("🔧 Check your email settings and try again")

if __name__ == "__main__":
    test_email()
