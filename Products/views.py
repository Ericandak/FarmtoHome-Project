from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product,Category,Stock,Cart_table,CartItem_table
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from django.db.models import Q
from django.template.loader import render_to_string

@login_required
def add_product(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('product_name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        image = request.FILES.get('image')
        is_active = request.POST.get('is_active') == 'on'  # Checkbox handling

        if not name:
            messages.error(request, 'Product name is required.')
            return render(request, 'Products/SellerIndex.html', {'categories': categories, 'error': 'Product name is required'})
        if not quantity or not quantity.isdigit():
            messages.error(request, 'Valid quantity is required.')
            return render(request, 'Products/SellerIndex.html', {'categories': categories, 'error': 'Valid quantity is required'})

        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            messages.error(request, 'Invalid category selected.')
            return render(request, 'Products/SellerIndex.html', {'categories': categories, 'error': 'Invalid category'})

        product = Product(
            seller=request.user,
            name=name,
            category=category,
            description=description,
            price=price,
            image=image,
            is_active=is_active
        )

        try:
            product.save()
            stock = Stock(
                product=product,
                quantity=int(quantity)
            )
            stock.save()
            messages.success(request, 'Product added successfully.')
            return redirect('add_product')
        except Exception as e:
            messages.error(request, f'Error saving product: {str(e)}')
            return render(request, 'Products/SellerIndex.html', {'categories': categories, 'error': 'Error saving product'})

    return render(request, 'Products/SellerIndex.html', {'categories': categories, 'username': request.user.username})

@login_required
def seller_home(request):
    categories = Category.objects.all()
    return render(request, 'Products/SellerIndex.html', {'categories': categories, 'username': request.user.username})
@login_required
def productlist(request):
    products = Product.objects.filter(seller=request.user)
    return render(request, 'Products/Productlist.html', {'products': products, 'username': request.user.username})

@login_required
def productedit(request, product_id):
    product = get_object_or_404(Product, id=product_id, seller=request.user)
    categories = Category.objects.all()

    if request.method == 'POST':
        product.name = request.POST.get('product_name')
        product.category_id = request.POST.get('category')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.is_active = request.POST.get('is_active') == 'on'  
        
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        
        product.save()

        stock = Stock.objects.get(product=product)
        stock.quantity = request.POST.get('quantity')
        stock.save()

        messages.success(request, 'Product updated successfully.')
        return redirect('sellerproductlist')

    return render(request, 'Products/productedit.html', {
        'product': product,
        'categories': categories,
        'username': request.user.username
    })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart_table.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem_table.objects.get_or_create(cart=cart, product=product)
    
    if not item_created:
        cart_item.quantity += 1
    else:
        cart_item.quantity = 1
    cart_item.save()
    
    messages.success(request, f"{product.name} has been added to your cart.")
    return redirect(reverse('home'))
@login_required
def cartview(request):
    user = request.user
    try:
        cart = Cart_table.objects.get(user=user)
        cart_items = cart.items.all()
        cart_item_count = cart_items.count()
        total = cart.total 
    except Cart_table.DoesNotExist:
        cart_items = []
        cart_item_count = 0
        total = 0

    context = {
        'username': user.username,
        'cart_items': cart_items,
        'cart_item_count': cart_item_count,
        'total': total,
    }
    return render(request, 'Products/cart.html', context)
@require_POST
@login_required
def update_cart_item(request):
    data = json.loads(request.body)
    item_id = data.get('item_id')
    action = data.get('action')
    try:
        cart_item = CartItem_table.objects.select_related('product').get(id=item_id, cart__user=request.user)
        stock = Stock.objects.get(product=cart_item.product)
        if action == 'increase':
            if cart_item.quantity < stock.quantity:
                cart_item.quantity += 1
            else:
                return JsonResponse({'status': 'error', 'message': 'Not enough stock available'})
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
            else:
                cart_item.delete()
                return JsonResponse({
                    'status': 'success',
                    'quantity': 0,
                    'subtotal': 0,
                    'total': cart_item.cart.total,
                })
        
        cart_item.save()
        cart_item.cart.refresh_from_db()
        return JsonResponse({
            'status': 'success',
            'quantity': cart_item.quantity,
            'subtotal': cart_item.subtotal,
            'total': cart_item.cart.total,
            'can_increase': cart_item.quantity < stock.quantity
        })

    except CartItem_table.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Cart item not found'}, status=404)
    except Stock.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Stock information not found'}, status=404)

@login_required
@require_POST
def deletecart(request):
    try:
        print("hi")
        data = json.loads(request.body)
        item_id = data.get('item_id')

        if not item_id:
            return JsonResponse({'status': 'error', 'message': 'Item ID is required'}, status=400)

        cart_item = CartItem_table.objects.get(id=item_id, cart__user=request.user)
        cart = cart_item.cart
        cart_item.delete()
        cart.refresh_from_db()

        return JsonResponse({
            'status': 'success',
            'total': cart.total,
            'is_cart_empty': cart.items.count() == 0  # Changed to boolean
        })
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    except CartItem_table.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Cart item not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def product_detail(request, product_id):
    user=request.user
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:6]
    try:
        cart = Cart_table.objects.get(user=user)
        cart_item_count = cart.items.count()
    except Cart_table.DoesNotExist:
        cart_item_count = 0
    context = {
        'product': product,
        'related_products': related_products,
        'username':user.username,
        'cart_item_count': cart_item_count
    }
    return render(request, 'Products/shop-detail.html', context)


@login_required
def search_results(request):
    user=request.user
    query = request.GET.get('q')
    category = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort = request.GET.get('sort', 'name')
    results=Product.objects.all()
    if query:
        results = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
    if category:
        results = results.filter(category_id=category)

    if min_price:
        results = results.filter(price__gte=min_price)

    if max_price:
        results = results.filter(price__lte=max_price)
    if sort == 'name':
        results = results.order_by('name')
    elif sort == '-name':
        results = results.order_by('-name')
    elif sort == 'price':
        results = results.order_by('price')
    elif sort == '-price':
        results = results.order_by('-price')
    results = results.order_by(sort)

    categories = Category.objects.all()

    context = {
        'results': results,
        'query': query,
        'categories': categories,
        'sort': sort, 
        'username':user.username # Add this line to pass the current sort to the template
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('Products/search_results_partial.html', context)
        return JsonResponse({'html': html, 'query': query})
    return render(request, 'Products/search_results.html', context)