from decimal import Decimal
import json
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import  UserRegisterForm , ProductUpdateForm, ProductForm
from decimal import Decimal
import json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import *
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import *
from django.db.models import Q
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import paypalrestsdk
import qrcode
from reportlab.platypus import Image  
from reportlab.lib.utils import ImageReader  

from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from django.core.mail import send_mail
from django.contrib import messages
from .forms import ContactForm
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

# Configurer PayPal
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET,
})



def home(request):
    # Récupérer les derniers produinumero_cnits ajoutés
    latest_products = Product.objects.select_related('owner').order_by('-created_at')[:8]
    
    # Récupérer les produits les plus populaires (à adapter selon vos besoins)
    popular_products = Product.objects.select_related('owner').order_by('?')[:6]
    
    # Récupérer quelques produits en vedette (random pour l'exemple)
    featured_products = Product.objects.select_related('owner').order_by('?')[:4]
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values()) if cart else 0

    context = {
        'latest_products': latest_products,
        'popular_products': popular_products,
        'featured_products': featured_products,
        'cart_count': cart_count,
    }
    return render(request, 'index.html', context)



@login_required(login_url='/login')
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.owner = request.user
            product.save()
            return redirect('catalogue')
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})

@login_required(login_url='/login')
def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, owner=request.user)
    if request.method == "POST":
        form = ProductUpdateForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ProductUpdateForm(instance=product)
    return render(request, 'update_product.html', {'form': form, 'product': product})

@login_required(login_url='/login')
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, owner=request.user)
    if request.method == "POST":
        product.delete()
        return redirect('home')
    return render(request, 'delete_product.html', {'product': product})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values()) if cart else 0
    context = {
        'product': product,
        'cart_count': cart_count,
    }
    return render(request, 'product_detail.html', context)


def catalogue(request):
    # Récupérer le terme de recherche
    query = request.GET.get('q', '')
    sort = request.GET.get('sort', 'recent')  # Par défaut, tri par date
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values()) if cart else 0

    # Construire la requête de base
    products = Product.objects.all()

    # Appliquer les filtres de recherche
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(owner__username__icontains=query)
        )

    # Filtre par prix
    if min_price:
        products = products.filter(price__gte=float(min_price))
    if max_price:
        products = products.filter(price__lte=float(max_price))

    # Appliquer le tri
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'recent':
        products = products.order_by('-created_at')
    elif sort == 'name':
        products = products.order_by('name')

    context = {
        'products': products,
        'current_query': query,
        'current_sort': sort,
        'current_min_price': min_price,
        'current_max_price': max_price,
        'cart_count': cart_count,  # Nombre d'articles dans le panier en cours de commande
    }

    return render(request, 'catalogue.html', context)




def user_profile(request, user_id):
    # Récupérer l'utilisateur ou renvoyer une erreur 404 si non trouvé
    user = get_object_or_404(User, id=user_id)
    
    
    # Récupérer les produits de l'utilisateur
    products = Product.objects.filter(owner=user)
    total_products = products.count()
    
    # Récupérer les commandes liées à l'utilisateur
    if user.role == 'farmer':
        # Si l'utilisateur est un agriculteur, compter les commandes de ses produits
        total_orders = Order.objects.filter(product__owner=user).count()
    else:
        # Si l'utilisateur est un acheteur ou fournisseur, compter ses commandes
        total_orders = Order.objects.filter(buyer=user).count()
    
    # Contexte pour le template
    context = {
        'user': user,
        'total_products': total_products,
        'total_orders': total_orders,
        'products': products,
    }
    
    return render(request, 'user_profile.html', context)





def payment_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values()) if cart else 0

    return render(request, 'payment/payment.html', {
        'product': product,
        'paypal_client_id': 'VOTRE_CLIENT_ID',
        'cart_count': cart_count,
    })



def handle_payment(request):
    if request.method == 'POST':
        try:
            # Pour PayPal (AJAX request)
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                product = Product.objects.get(id=data.get('productId'))
                quantity = int(data.get('quantity'))
                amount = float(data.get('amount')) * 600  # Conversion USD to FCFA
                
                order = Order.objects.create(
                    buyer=request.user,
                    product=product,
                    quantity=quantity,
                    total_amount=amount,
                    payment_id=data.get('orderID'),
                    buyer_email=data.get('payerEmail'),
                    status='COMPLETED'
                )
                
                Payment.objects.create(
                    order=order,
                    amount=amount,
                    payment_method='paypal',
                    transaction_id=data.get('orderID'),
                    status='completed'
                )
                
                return JsonResponse({'status': 'success', 'redirect_url': f'/payment/success/{order.id}/'})
            
            # Pour paiement normal (form submit)
            else:
                product = Product.objects.get(id=request.POST.get('product_id'))
                quantity = int(request.POST.get('quantity'))
                amount = float(request.POST.get('total_amount'))
                
                order = Order.objects.create(
                    buyer=request.user,
                    product=product,
                    quantity=quantity,
                    total_amount=amount,
                    payment_id=f'NORMAL-{uuid.uuid4()}',
                    buyer_email=request.user.email,
                    status='COMPLETED'
                )
                
                Payment.objects.create(
                    order=order,
                    amount=amount,
                    payment_method='normal',
                    transaction_id=order.payment_id,
                    status='completed'
                )
                
                return redirect(f'/payment/success/{order.id}/')
                
        except Exception as e:
            messages.error(request, f'Erreur lors du paiement: {str(e)}')
            return redirect('/')
    
    return redirect('/')

def success_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'payment/payment_success.html', {'order': order})



def download_invoice(request, order_id):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm, cm
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle, Image, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    import qrcode
    from io import BytesIO
    
    order = get_object_or_404(Order, id=order_id)
    buffer = BytesIO()
    
    # Configuration de la page
    width, height = A4
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.black,
        alignment=1,  # Center
        spaceAfter=6
    )
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        leading=14
    )
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.black,
        spaceBefore=12,
        spaceAfter=6
    )
    
    # Couleurs de l'entreprise
    orange_color = colors.Color(1, 0.5, 0)  # Orange
    black_color = colors.black
    
    # En-tête avec logo et infos entreprise
    # Bordure orange en haut
    p.setStrokeColor(orange_color)
    p.setLineWidth(5)
    p.line(1*cm, height-1*cm, width-1*cm, height-1*cm)
    
    # Logo (simulé par un rectangle avec texte)
    p.setFillColor(orange_color)
    p.rect(1.5*cm, height-4*cm, 3*cm, 2*cm, fill=1)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(3*cm, height-3*cm, "KF")
    
    # Informations entreprise
    p.setFillColor(black_color)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(5*cm, height-2.3*cm, "KmerFusion")
    p.setFont("Helvetica", 10)
    p.drawString(5*cm, height-2.8*cm, "123 Avenue Principale, Yaoundé, Cameroun")
    p.drawString(5*cm, height-3.3*cm, "www.kmerfusion.com | support@kmerfusion.com")
    p.drawString(5*cm, height-3.8*cm, "Tél: +237 123 456 789 | RCCM: 12345-CAM-2023")
    
    # Titre Facture
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2, height-5.5*cm, "FACTURE")
    
    # Numéro et date de facture
    p.setFillColor(orange_color)
    p.rect(width-6*cm, height-5*cm, 4.5*cm, 3*cm, fill=0)
    p.setFillColor(black_color)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(width-5.8*cm, height-2.5*cm, "N° Facture:")
    p.drawString(width-5.8*cm, height-3*cm, "Date:")
    p.drawString(width-5.8*cm, height-3.5*cm, "Réf:")
    p.setFont("Helvetica", 10)
    p.drawString(width-3.5*cm, height-2.5*cm, f"F-{order.id:06d}")
    p.drawString(width-3.5*cm, height-3*cm, f"{order.created_at.strftime('%d/%m/%Y')}")
    p.drawString(width-3.5*cm, height-3.5*cm, f"CD-{order.id:06d}")
    
    # Informations client
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1.5*cm, height-7*cm, "Informations client")
    p.setStrokeColor(orange_color)
    p.setLineWidth(1)
    p.line(1.5*cm, height-7.2*cm, 6*cm, height-7.2*cm)
    
    # Cadre client
    p.setStrokeColor(colors.lightgrey)
    p.rect(1.5*cm, height-10*cm, 8*cm, 2.5*cm, fill=0)
    
    p.setFont("Helvetica", 10)
    y_position = height - 7.8*cm
    p.drawString(2*cm, y_position, f"Nom: {order.buyer.username}")
    y_position -= 0.5*cm
    p.drawString(2*cm, y_position, f"Email: {order.buyer_email}")
    
    if hasattr(order.buyer, 'phone') and order.buyer.phone:
        y_position -= 0.5*cm
        p.drawString(2*cm, y_position, f"Téléphone: {order.buyer.phone}")
    
    if hasattr(order.buyer, 'numero_cni') and order.buyer.numero_cni:
        y_position -= 0.5*cm
        p.drawString(2*cm, y_position, f"CNI: {order.buyer.numero_cni}")
    
    # Générer QR code (contient le lien vers la facture)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=3,
        border=4,
    )
    qr.add_data(f"https://kmerfusion.com/facture/{order.id}")
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer)
    qr_buffer.seek(0)
    
    # Placer le QR code
    p.drawImage(ImageReader(qr_buffer), width-4.5*cm, height-10*cm, width=3*cm, height=3*cm)
    p.setFont("Helvetica", 8)
    p.drawCentredString(width-3*cm, height-10.5*cm, "Scannez pour vérifier")
    
    # Détails de la commande - Tableau
    data = [
        ["Description", "Quantité", "Prix unitaire", "Total"]
    ]
    data.append([
        order.product.name,
        str(order.quantity),
        f"{order.product.price:,} FCFA".replace(',', ' '),
        f"{order.total_amount:,} FCFA".replace(',', ' ')
    ])
    
    # Ajouter des lignes vides pour un meilleur aspect
    for _ in range(3):  
        data.append(["", "", "", ""])
    
    table = Table(data, colWidths=[9*cm, 2*cm, 3.5*cm, 3.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), orange_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 1), (3, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
    ]))
    
    table.wrapOn(p, width, height)
    table.drawOn(p, 1.5*cm, height-15*cm)
    
    # Résumé des coûts - Version corrigée
    p.setFont("Helvetica-Bold", 10)
    p.drawString(11.5*cm, height-16*cm, "Sous-total:")
    p.drawString(11.5*cm, height-16.7*cm, "TVA (0%):")
    p.drawString(11.5*cm, height-18*cm, "Montant total:")  # Position descendue pour laisser de l'espace

    p.setFont("Helvetica", 10)
    p.drawRightString(width-1.5*cm, height-16*cm, f"{order.total_amount:,} FCFA".replace(',', ' '))
    p.drawRightString(width-1.5*cm, height-16.7*cm, "0 FCFA")

    # Rectangle coloré pour le montant total (déplacé pour éviter le chevauchement avec la TVA)
    p.setFillColor(orange_color)
    p.rect(11*cm, height-18.5*cm, width-12.5*cm, 1*cm, fill=1)  # Position ajustée
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 12)
    # Position du texte ajustée pour être au milieu du rectangle
    p.drawRightString(width-1.5*cm, height-17.9*cm, f"{order.total_amount:,} FCFA".replace(',', ' '))  
    # Informations de paiement
    p.setFillColor(black_color)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1.5*cm, height-18.5*cm, "Informations de paiement")
    p.setStrokeColor(orange_color)
    p.line(1.5*cm, height-18.7*cm, 7*cm, height-18.7*cm)
    
    p.setFont("Helvetica", 10)
    method = "Paiement Normal"
    if hasattr(order, 'payment') and order.payment:
        method = order.payment.get_payment_method_display()
    p.drawString(1.5*cm, height-19.5*cm, f"Méthode: {method}")
    p.drawString(1.5*cm, height-20*cm, f"Date: {order.created_at.strftime('%d/%m/%Y %H:%M')}")
    p.drawString(1.5*cm, height-20.5*cm, f"Statut: Payé")
    
    # Notes et conditions
    p.setFont("Helvetica-Bold", 10)
    p.drawString(1.5*cm, height-22*cm, "Notes et conditions:")
    p.setFont("Helvetica", 8)
    p.drawString(1.5*cm, height-22.7*cm, "• Cette facture est une preuve de paiement et doit être conservée pour référence future")
    p.drawString(1.5*cm, height-23.2*cm, "• Pour toute assistance, veuillez contacter notre service client au +237 672-456-789")
    p.drawString(1.5*cm, height-23.7*cm, "• Les retours sont acceptés dans un délai de 7 jours suivant la livraison")
    
    # Pied de page
    p.setStrokeColor(orange_color)
    p.setLineWidth(5)
    p.line(1*cm, 1*cm, width-1*cm, 1*cm)
    
    p.setFont("Helvetica", 8)
    p.drawCentredString(width/2, 0.7*cm, "KmerFusion SARL - RCCM 12345-CAM-2023 - Yaoundé, Cameroun")
    p.drawCentredString(width/2, 0.4*cm, "www.kmerfusion.com - support@kmerfusion.com - +237 672-456-789")
    
    # Réference de facturation unique
    p.rotate(90)
    p.setFillColor(colors.lightgrey)
    p.setFont("Helvetica", 6)
    p.drawString(2*cm, -width+0.5*cm, f"REF: {order.id}-{order.created_at.strftime('%Y%m%d%H%M%S')}")
    p.rotate(-90)
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_{order.id}.pdf"'
    
    return response


def payment_success(request):
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values()) if cart else 0
    return render(request, 'payment_success.html')




def payment_cancel(request):
    return render(request, 'payment/cancelled.html')




def contact(request):
    cart = request.session.get('cart', {})
    cart_count = sum(cart.values()) if cart else 0
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Récupérer les données du formulaire
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            # Préparer le message
            email_message = f"""
            Nouveau message de : {name}
            Email : {email}
            
            {message}
            """
            
            # Envoyer l'email
            try:
                send_mail(
                    subject=f"Contact AgriConnect: {subject}",
                    message=email_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.DEFAULT_FROM_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, "Votre message a été envoyé avec succès !")
                return redirect('contact')
            except Exception as e:
                messages.error(request, "Une erreur s'est produite lors de l'envoi du message. Veuillez réessayer.")
    else:
        form = ContactForm()

    
    return render(request, 'contact.html', {'form': form, 'cart_count': cart_count})


def about(request):
    return render(request, 'about.html')


def add_to_cart(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = str(data.get('product_id'))
            
            # Initialiser le panier s'il n'existe pas
            if 'cart' not in request.session:
                request.session['cart'] = {}
            
            # Ajouter le produit au panier
            cart = request.session['cart']
            if product_id in cart:
                cart[product_id] += 1
            else:
                cart[product_id] = 1
            
            request.session.modified = True
            
            # Compter le nombre total d'articles
            cart_count = sum(cart.values())
            
            return JsonResponse({
                'success': True,
                'cart_count': cart_count
            })
        except Exception as e:
            print(f"Erreur : {str(e)}")  # Pour le débogage
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False})

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Order, Payment, Product
import paypalrestsdk
import json

# Configure PayPal
paypalrestsdk.configure({
    "mode": "sandbox",
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_CLIENT_SECRET
})

def cart_view(request):
    cart = request.session.get('cart', {})
    print("Cart content:", cart)
    cart_count = sum(cart.values()) if cart else 0
    cart_items = []
    total = 0
    print("Cartcount_:", cart_count)
    
    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        subtotal = product.price * quantity
        total += subtotal
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal
        })
    
    return render(request, 'achat.html', {
        'cart_items': cart_items,
        'total': total,
        'cart_count': cart_count
    })



def create_order(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        cart_items = request.session.get('cart', {})
        
        if not cart_items:
            return JsonResponse({'success': False, 'error': 'Panier vide'})

        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'country', 'city', 'address']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False, 
                    'error': f'Le champ {field} est requis'
                })

        # Calculate total amount
        total_amount = 0
        ordered_items = []
        for product_id, quantity in cart_items.items():
            product = Product.objects.get(id=product_id)
            total_amount += product.price * quantity
            ordered_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': product.price * quantity
            })

        # Create order record
        order = Order.objects.create(
            buyer=None,  # Anonymous user
            total_amount=total_amount,
            buyer_name=data.get('name'),
            buyer_email=data.get('email'),
            shipping_address=data.get('address'),
            shipping_country=data.get('country'),
            shipping_city=data.get('city'),
            shipping_phone=data.get('phone'),
            status='PENDING'
        )

        # Create order items
        for item in ordered_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                unit_price=item['product'].price,
                subtotal=item['subtotal']
            )

        # Store order ID in session
        request.session['last_order_id'] = order.id

        # Initialize PayPal payment
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": request.build_absolute_uri(f'/payment-success/{order.id}/'),
                "cancel_url": request.build_absolute_uri(f'/payment-cancelled/{order.id}/')
            },
            "transactions": [{
                "amount": {
                    "total": str(total_amount),
                    "currency": "EUR"
                },
                "description": f"Commande #{order.id}"
            }]
        })

        if payment.create():
            # Record payment attempt
            Payment.objects.create(
                order=order,
                amount=total_amount,
                payment_method='paypal',
                status='pending',
                payment_id=payment.id
            )

            # Clear shopping cart
            request.session['cart'] = {}
            request.session.modified = True

            # Return PayPal redirect URL
            for link in payment.links:
                if link.method == "REDIRECT":
                    return JsonResponse({
                        'success': True,
                        'redirect_url': link.href
                    })

        return JsonResponse({
            'success': False,
            'error': 'Erreur lors de la création du paiement'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Format de données invalide'
        })
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Produit non trouvé'
        })
    except Exception as e:
        print(f"Order error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Une erreur est survenue lors de la création de la commande'
        })


def payment_success(request, order_id):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')
    
    try:
        payment = paypalrestsdk.Payment.find(payment_id)
        if payment.execute({"payer_id": payer_id}):
            # Update order and payment
            order = Order.objects.get(id=order_id)
            order.status = 'COMPLETED'
            order.payment_id = payment_id
            order.save()

            payment_obj = Payment.objects.get(order=order)
            payment_obj.status = 'completed'
            payment_obj.transaction_id = payment_id
            payment_obj.save()

            # Clear any remaining cart data
            request.session['cart'] = {}
            request.session.modified = True

            return render(request, 'payment_success.html', {'order': order})
    except Exception as e:
        print(f"Payment error: {str(e)}")
    
    return redirect('payment_failed')

def payment_cancelled(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        order.status = 'CANCELLED'
        order.save()

        payment = Payment.objects.get(order=order)
        payment.status = 'cancelled'
        payment.save()
    except Exception as e:
        print(f"Cancel error: {str(e)}")

    return render(request, 'payment_cancelled.html')

@csrf_exempt
def update_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = str(data.get('product_id'))
        quantity = int(data.get('quantity'))
        
        cart = request.session.get('cart', {})
        
        if quantity > 0:
            cart[product_id] = quantity
        else:
            if product_id in cart:
                del cart[product_id]
                
        request.session['cart'] = cart
        request.session.modified = True
        
        # Recalculer le total
        total = sum(Product.objects.get(id=pid).price * qty 
                   for pid, qty in cart.items())
        
        # Calculer le sous-total pour l'article modifié
        item_total = Product.objects.get(id=product_id).price * quantity if quantity > 0 else 0
        
        return JsonResponse({
            'success': True,
            'total': float(total),
            'item_total': float(item_total)
        })
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

def remove_from_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        
        cart = request.session.get('cart', {})
        if product_id in cart:
            del cart[product_id]
            request.session['cart'] = cart
            request.session.modified = True
            
        total = sum(Product.objects.get(id=pid).price * qty 
                   for pid, qty in cart.items())
            
        return JsonResponse({
            'success': True,
            'total': float(total)
        })
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})