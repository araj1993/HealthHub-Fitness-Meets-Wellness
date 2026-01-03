from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.conf import settings
from datetime import datetime
import os


def generate_membership_receipt(membership, file_path):
    """
    Generate a PDF receipt for user membership registration
    
    Args:
        membership: UserMembership instance
        file_path: Full path where PDF will be saved
    """
    
    # Create the PDF object
    doc = SimpleDocTemplate(file_path, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2C3E50'),
    )
    
    # Header
    title = Paragraph("<b>HealthHub - Payment Receipt</b>", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2 * inch))
    
    # Receipt Info
    receipt_info = [
        ['Registration ID:', str(membership.registration_id)],
        ['Receipt Date:', datetime.now().strftime('%B %d, %Y')],
        ['Receipt Number:', str(membership.receipt.receipt_number) if hasattr(membership, 'receipt') else 'N/A'],
    ]
    
    receipt_table = Table(receipt_info, colWidths=[2*inch, 4*inch])
    receipt_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7F8C8D')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2C3E50')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(receipt_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # User Information Section
    elements.append(Paragraph("<b>Member Information</b>", heading_style))
    
    user_info = [
        ['Name:', membership.user.full_name],
        ['Email:', membership.user.email],
        ['Phone:', membership.user.phone_number],
        ['Age:', str(membership.age)],
        ['Weight:', f"{membership.current_weight} kg"],
        ['Date of Joining:', membership.date_of_joining.strftime('%B %d, %Y')],
    ]
    
    user_table = Table(user_info, colWidths=[2*inch, 4*inch])
    user_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
    ]))
    elements.append(user_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Membership Details Section
    elements.append(Paragraph("<b>Membership Details</b>", heading_style))
    
    tier_name = membership.get_membership_tier_display()
    membership_details = [
        ['Membership Type:', tier_name],
    ]
    
    # Add tier-specific amenities
    if membership.membership_tier == 'L1':
        amenities = ['Basic Gym Access', 'Standard Equipment']
    elif membership.membership_tier == 'L2':
        amenities = [
            'All L1 Features',
            'AI Workout Planner',
            'Nutrition Recommendations',
            'Weekly Performance Insights',
            'Stress & Activity Analysis'
        ]
        if membership.extra_protein_needed:
            amenities.append('Extra Protein Supplementation')
    elif membership.membership_tier == 'L3':
        amenities = [
            'All L1 + L2 Features',
            'Daily Protein Shake (40g) - Your favorite flavor!'
        ]
        
        # Add L3 addons with trainer info
        for addon in membership.l3_addons.all():
            addon_text = addon.get_addon_type_display()
            if addon.addon_type == 'TRAINER' and addon.assigned_trainer:
                trainer = addon.assigned_trainer
                profile = getattr(trainer, 'trainer_profile', None)
                if profile:
                    addon_text += f" - {trainer.full_name} ({profile.specialization})"
                else:
                    addon_text += f" - {trainer.full_name}"
            amenities.append(addon_text)
    else:
        amenities = []
    
    membership_details.append(['Amenities:', ', '.join(amenities) if len(amenities) <= 3 else '\n'.join(amenities)])
    
    if membership.pay_monthly_in_advance:
        membership_details.append(['Advance Payment:', f'{membership.months_selected} months'])
    
    membership_table = Table(membership_details, colWidths=[2*inch, 4*inch])
    membership_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
    ]))
    elements.append(membership_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Fee Breakdown Section
    elements.append(Paragraph("<b>Fee Breakdown</b>", heading_style))
    
    fee_data = [
        ['Description', 'Amount (₹)'],
        ['Base Registration Fee', f'₹{membership.base_registration_fee:,.2f}'],
    ]
    
    if membership.monthly_fee > 0:
        if membership.membership_tier == 'L1':
            monthly_rate = 1500
        elif membership.membership_tier in ['L2', 'L3']:
            monthly_rate = 2500
        else:
            monthly_rate = 0
        
        fee_data.append([
            f'Monthly Fee ({membership.months_selected} months @ ₹{monthly_rate}/month)',
            f'₹{(monthly_rate * membership.months_selected):,.2f}'
        ])
        
        if membership.discount_amount > 0:
            fee_data.append([
                f'Discount (₹200 × {membership.months_selected - 2} extra months)',
                f'- ₹{membership.discount_amount:,.2f}'
            ])
    
    if membership.addon_fees > 0:
        fee_data.append(['L3 Add-ons', f'₹{membership.addon_fees:,.2f}'])
    
    fee_data.append(['', ''])  # Separator
    fee_data.append(['<b>Total Amount Paid</b>', f'<b>₹{membership.total_amount:,.2f}</b>'])
    
    fee_table = Table(fee_data, colWidths=[4*inch, 2*inch])
    fee_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
        ('GRID', (0, 0), (-1, -3), 0.5, colors.HexColor('#BDC3C7')),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#27AE60')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#D5F4E6')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(fee_table)
    elements.append(Spacer(1, 0.5 * inch))
    
    # Footer
    footer_text = """
    <para align=center>
    <b>Thank you for joining HealthHub!</b><br/>
    For any queries, contact us at support@healthhub.com or call +1-800-FITNESS<br/>
    <i>This is a computer-generated receipt and does not require a signature.</i>
    </para>
    """
    footer = Paragraph(footer_text, normal_style)
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    
    return file_path
