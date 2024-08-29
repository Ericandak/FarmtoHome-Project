
# Create your views here.
from django.shortcuts import render,redirect,reverse,get_object_or_404
from django.views.decorators.cache import never_cache
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse,JsonResponse
import pyotp
from django.core.mail import send_mail
import random
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_log,logout
from  django.contrib.auth.hashers import make_password
from .models import Address_table,State,Role,SellerDetails
from Products.models import Category,Product,CartItem_table,Cart_table
from django.db import IntegrityError
from django.views.decorators.http import require_GET
from allauth.account.utils import user_username
from django.templatetags.static import static
from django.db.models import Sum
from django.db.models.functions import TruncMonth,TruncDate
from orders.models import Order
import json
from django.utils import timezone
from datetime import timedelta


# Create your views here.
User = get_user_model()

def Registration(request):
    return render(request, 'Users/Login.html')

def UserRegistration(request):
    if request.method == 'POST':
        # Retrieve form data
        request.session['registration_data'] = {
            'first_name': request.POST.get('first-name'),
            'last_name': request.POST.get('last-name'),
            'email': request.POST.get('your_email'),
            'phone': request.POST.get('phone'),
            'password': request.POST.get('your_cpassword'),
        }
        reg=request.session.get('registration_data')
        email=reg['email']
        if User.objects.filter(email=email).exists():
            error_message = "Email is already registered."
            cont = {
                'background_image_url': static('assets/img/crops.jpg'),
                'error_message': error_message
                }
            return render(request, 'Users/Registration.html', cont)
        else:
        # Redirect to send OTP email
            return redirect('send_otp_email')
    context = {
        'background_image_url': static('assets/img/crops.jpg')
        }

    return render(request, 'Users/Registration.html',context)
    


def send_otp_email(request):
    # Retrieve registration data from session
    registration_data = request.session.get('registration_data')
    if not registration_data:
        return redirect('user_registration')  # Redirect to registration if session data is missing

    # Generate OTP using pyotp library
    otp_secret = pyotp.random_base32()
    totp = pyotp.TOTP(otp_secret)
    otp = totp.now()
    request.session['otp']=otp
    # Send OTP via email (example using Django's send_mail)
    subject = 'OTP Verification'
    message = f'Your OTP for registration is: {otp}'
    from_email = 'farmtohome584@gmail.com'  # Replace with your email
    to_email = registration_data['email']  # Use the email provided in registration form

    send_mail(subject, message, from_email, [to_email])

    # Pass OTP to template for verification
    context = {
        'otp': otp,
        'email': to_email,  # Passing email to pre-fill the form (optional)
    }

    return render(request, 'Users/send_otp_email.html', context)



def verify_otp(request):
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        stored_email = request.POST.get('email')  # Retrieve email from the form

        # Retrieve OTP from session
        stored_otp = request.session.get('otp')
        if stored_otp is None:
            messages.error(request, 'OTP expired. Please try again.')
            return redirect('user_registration')  # Redirect to registration page if OTP is expired

        # Validate OTP
        if user_otp == stored_otp:
            # Save registration data to database
            registration_data = request.session.get('registration_data')
            suffix = random.randint(1000, 9999)  # Adjust range as needed
            username = registration_data['first_name'] + str(suffix)
            while User.objects.filter(username=username).exists():
              suffix = random.randint(1000, 9999)  # Generate new suffix
              username = registration_data['first_name'] + str(suffix)
       # Check if the username already exists
            
            if registration_data:
                try:
                # Fetch the Role instance for 'Customer'
                    customer_role = Role.objects.get(name='Customer')
                except Role.DoesNotExist:
                    messages.error(request, 'Role "Customer" not found. Please contact support.')
                    return redirect('user_registration')

                hashed_password = make_password(registration_data['password'])
                # Assuming you have a model named `User` for user registration
                new_user = User.objects.create(
                    username=username,
                    first_name=registration_data['first_name'],
                    last_name=registration_data['last_name'],
                    email=registration_data['email'],
                    phone_number=registration_data['phone'],
                    password=hashed_password
                )
                new_user.role.set([customer_role])
                # Clear session data after registration
                del request.session['registration_data']
                del request.session['otp']
                
                messages.success(request, 'Registration successful!')
                return redirect('Login')  # Redirect to home or login page after successful registration
            else:
                messages.error(request, 'Registration data not found. Please try again.')
                return redirect('user_registration')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
            return redirect('user_registration')  # Redirect to registration page if OTP is incorrect

    return render(request, 'Users/verify_otp.html')
def Login(request):
    if request.user.is_authenticated:
        # Check if the user just completed social login
        if 'socialaccount_login' in request.session:
            del request.session['socialaccount_login']

        if not request.user.role.exists():
            customer_role, created = Role.objects.get_or_create(name='Customer')
            request.user.role.add(customer_role)
            request.user.save()

        try:
            address = Address_table.objects.get(user=request.user)
            if address.state is None:
                return redirect('stateentry')
        except Address_table.DoesNotExist:
            return redirect('stateentry')
        return redirect('home')
    if request.method == 'POST':
        email = request.POST.get('your_email')
        password = request.POST.get('your_password')
        print(f"Attempting login with email: {email}")

        # Check if the user exists in the database
        try:
            user_obj = User.objects.get(email=email)
            print(f"User found: {user_obj.username}, Email: {user_obj.email}")
        except User.DoesNotExist:
            print(f"No user found with email: {email}")
            user_obj = None

        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            print(f"Authentication successful for user: {user.username}")
            auth_log(request, user)
            request.session['username'] = user.username
            request.session.save()
            print(f"Session set in Login: {request.session.get('username')}")
            roles = user.role.all()
            role_names = list(roles.values_list('name', flat=True))
            print(f"User roles: {role_names}")

            if 'Admin' in role_names:
                return redirect('adminlog')
            elif 'Customer' in role_names or 'Seller' in role_names:
                return handle_customer_seller_login(user, role_names)
            else:
                error_message = "User role not recognized."
                return render(request, 'Users/Login.html', {'error': error_message})
        else:
            print("Authentication failed")
            if user_obj:
                print("User exists but authentication failed. Possible password mismatch.")
            error_message = "Invalid email or password."
            return render(request, 'Users/Login.html', {'error': error_message})

    return render(request, 'Users/Login.html')

def handle_customer_seller_login(user, role_names):
    if 'Customer' in role_names:
        try:
            address = Address_table.objects.get(user=user)
            if address.state is None:
                return redirect('stateentry')
            elif not address.address or not address.city or not address.zip_code:
                return redirect('address_entry')
            elif 'Seller' in role_names:
                return handle_seller_part(user)
            else:
                return redirect('home')
        except Address_table.DoesNotExist:
            return redirect('stateentry')
    elif 'Seller' in role_names:
        return handle_seller_part(user)

def handle_seller_part(user):
    try:
        seller_details = SellerDetails.objects.get(user=user)
        if seller_details.state is None:
            return redirect('stateentry')
        elif not seller_details.FarmAddress or not seller_details.Farmcity or not seller_details.Farmzip_code:
            return redirect('SellerDetails')
        else:
            return redirect('SellerHome')
    except SellerDetails.DoesNotExist:
        return redirect('stateentry')

@never_cache
@login_required
def auth_logout(request):
    logout(request)
    return redirect('Login')
@login_required
def home(request):
    user = request.user
    cart_item_count = 0
    products = Product.objects.filter(is_active=True)  # Fetch all active products
    categories = Category.objects.all()
    try:
        cart = Cart_table.objects.get(user=user)
        cart_item_count = cart.items.count()
    except Cart_table.DoesNotExist:
        pass  # If the cart doesn't exist, count remains 0
    print(f"Number of products: {products.count()}")
    username = request.session.get('username') or user_username(user)
    if not username:
        username = user.email.split('@')[0] if user.email else 'User'
    
    context = {
        'username': username,
        'products': products,
        'categories': categories,
        'cart_item_count': cart_item_count
    }
    
    return render(request, 'Products/index.html', context)
@login_required
def customer_dashboard_with_seller_link(request):
    print("Session keys:", request.session.keys())
    username = request.session.get('username')
    print(f"Session retrieved in dashboard: {username}")
    if not username:
        print("User object:", request.user)
        print("Is authenticated:", request.user.is_authenticated)
        return redirect('Login')

    return render(request, 'Products/index.html', {'has_seller_role': True,'username':username})


@login_required
def stateentry(request):
    user = request.user
    if request.method == 'POST':
        state_name = request.POST.get('state')
        country_name = request.POST.get('country')
        
        if state_name and country_name:
            state, created = State.objects.get_or_create(name=state_name, country=country_name)
            roles = user.role.all()
            role_names = set(roles.values_list('name', flat=True))

            # Check for Customer role
            if 'Customer' in role_names:
                try:
                    address = Address_table.objects.get(user=user)
                    if not address.address or not address.city or not address.zip_code:
                        return redirect('address_entry', state_id=state.id)
                except Address_table.DoesNotExist:
                    return redirect('address_entry', state_id=state.id)

            # Check for Seller role
            if 'Seller' in role_names:
                try:
                    seller_details = SellerDetails.objects.get(user=user)
                    if not seller_details.FarmAddress or not seller_details.Farmcity or not seller_details.Farmzip:
                        return redirect('SellerDetails', state_id=state.id)
                except SellerDetails.DoesNotExist:
                    return redirect('SellerDetails', state_id=state.id)

            # If all necessary details are filled, redirect to appropriate page
            if 'Seller' in role_names:
                return redirect('SellerHome')
            else:
                return redirect('home')

        else:
            error_message = "Both state and country are required."
            countries = State.objects.values_list('country', flat=True).distinct()
            return render(request, 'Users/Stateentry.html', {'error': error_message, 'countries': countries})

    countries = State.objects.values_list('country', flat=True).distinct()
    return render(request, 'Users/Stateentry.html', {'countries': countries})

@login_required
@require_GET
def load_states(request):
    country = request.GET.get('country')
    if not country:
        return JsonResponse([], safe=False)
    
    try:
        states = list(State.objects.filter(country=country)
                      .values('id', 'name')
                      .distinct()
                      .order_by('name'))
        return JsonResponse(states, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)



@login_required
def addressentry(request, state_id):
    if request.method == 'POST':
        street = request.POST.get('Landmark')
        city = request.POST.get('your_city')
        zipcode = request.POST.get('your_pin')
        state = get_object_or_404(State, id=state_id)
        
        if street and city and zipcode:
            Address_table.objects.create(
            user=request.user,
            address=street,
            city=city,
            zip_code=zipcode,
            state=state
        )
            try:
                return redirect('home')  # Redirect to the home page or another appropriate page
            except IntegrityError as e:
                # Catch and print any IntegrityErrors
                print(f"IntegrityError: {e}")
                error_message = "There was an error saving your address. Please try again."
                return render(request, 'Users/addressentry.html', {
                    'error': error_message,
                    'state': state_id,
                    'address': addresss
                })
        else:
            error_message = "All fields (street, city, and zipcode) are required."
            return render(request, 'Users/addressentry.html', {
                'error': error_message,
                'state': state_id,
                'address': addresss
            })

    return render(request, 'Users/addressentry.html', {
        'state': state_id
    })
@login_required
def profile_update(request):
    user=request.user
    username = user.username
    user = None
    address = None
    state = None
    countries = []

    if username:
        try:
            user = get_object_or_404(User, username=username)
            address = get_object_or_404(Address_table, user=user)
            state = address.state if address else None
        except (User.DoesNotExist, Address_table.DoesNotExist):
            user = None
            address = None

        if request.method == 'POST':
            if user:
                user.email = request.POST.get('email', user.email)
                user.first_name = request.POST.get('first_name', user.first_name)
                user.last_name = request.POST.get('last_name', user.last_name)
                user.phone_number = request.POST.get('phone_number', user.phone_number)
                user.save()

            if address:
                address.address = request.POST.get('street', address.address)
                address.city = request.POST.get('city', address.city)
                address.zip_code = request.POST.get('zip_code', address.zip_code)
                new_state = request.POST.get('state')
                new_country = request.POST.get('country')
                if new_state and new_country:
                    state, created = State.objects.get_or_create(name=new_state, country=new_country)
                    address.state = state
                address.save()

            messages.success(request, "Profile updated successfully.")
            return redirect('profile_edit')

        if state:
            countries = State.objects.values_list('country', flat=True).distinct()
    else:
        messages.error(request, "User not found in session.")
        return redirect('Login')  # Redirect to login page if username is not in session

    context = {
        'user': user,
        'address': address,
        'state': state,
        'countries': countries
    }
    return render(request, 'Users/User_profile.html', context)
@login_required
def SellerProfile(request):
    user = request.user
    categories=Category.objects.all()
    context = {
        'username': user.username,
        'categories':categories

        # Add any other user details you want to pass to the template
    }
    return render(request,'Products/SellerIndex.html',context)
def SellerRegister(request):
    if request.method == 'POST':
        # Retrieve form data
        request.session['seller_data'] = {
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone'),
            'password': request.POST.get('cpassword'),
        }
        reg=request.session.get('seller_data')
        email=reg['email']
        try:
            existing_user = User.objects.get(email=email)
            existing_roles = existing_user.role.values_list('name', flat=True)
            if 'Seller' in existing_roles:
                # User is already registered as Seller
                messages.info(request, 'Email is already registered as a Seller.')
                return redirect('Login')  # or handle accordingly
            else:
                # Handle case for users with other roles
                context = {
                    'update_roles': True,
                    'background_image_url': static('assets/img/crops.jpg'),
                    'existing_user': existing_user
                }
                return render(request, 'Users/SellerReg.html', context)

        except User.DoesNotExist:
            return redirect('seller_send_otp_email')

            
    context = {
        'background_image_url': static('assets/img/crops.jpg')
        }
    return render(request,'Users/SellerReg.html',context)
def update_roles(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            seller_role, created = Role.objects.get_or_create(name='Seller')
            
            # Update the user's roles
            if not user.role.filter(name='Seller').exists():
                user.role.add(seller_role)
                messages.success(request, 'Role added successfully.')
            else:
                messages.info(request, 'Role already exists for this user.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
        except Role.DoesNotExist:
            messages.error(request, 'Role not found.')

        return redirect('Login')

    return redirect('SellerReg')
def seller_send_otp_email(request):
    # Retrieve registration data from session
    registration_data = request.session.get('seller_data')
    if not registration_data:
        return redirect('SellerReg')  # Redirect to registration if session data is missing

    # Generate OTP using pyotp library
    otp_secret = pyotp.random_base32()
    totp = pyotp.TOTP(otp_secret)
    otp = totp.now()
    request.session['otp']=otp
    # Send OTP via email (example using Django's send_mail)
    subject = 'OTP Verification'
    message = f'Your OTP for registration for the seller account is: {otp}'
    from_email = 'farmtohome584@gmail.com'  # your email
    to_email = registration_data['email']  # email provided in registration form

    send_mail(subject, message, from_email, [to_email])

    # Pass OTP to template for verification
    context = {
        'otp': otp,
        'email': to_email,  # Passing email to pre-fill the form
    }

    return render(request, 'Users/seller_send_otp_email.html', context)
def verify_otp_seller(request):
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        stored_email = request.POST.get('email')  # Retrieve email from the form

        # Retrieve OTP from session
        stored_otp = request.session.get('otp')
        if stored_otp is None:
            messages.error(request, 'OTP expired. Please try again.')
            return redirect('SellerReg')  # Redirect to registration page if OTP is expired

        # Validate OTP
        if user_otp == stored_otp:
            # Save registration data to database
            registration_data = request.session.get('seller_data')
            suffix = random.randint(1000, 9999)  # Adjust range as needed
            username = registration_data['first_name'] + str(suffix)
            while User.objects.filter(username=username).exists():
              suffix = random.randint(1000, 9999)  # Generate new suffix
              username = registration_data['first_name'] + str(suffix)
       # Check if the username already exists
            
            if registration_data:
                seller_role = Role.objects.get(name='Seller')
                hashed_password = make_password(registration_data['password'])
                # Assuming you have a model named `User` for user registration
                new_user = User.objects.create(
                    username=username,
                    first_name=registration_data['first_name'],
                    last_name=registration_data['last_name'],
                    email=registration_data['email'],
                    phone_number=registration_data['phone'],
                    password=hashed_password,
                )
                new_user.role.set([seller_role])
                # Clear session data after registration
                del request.session['seller_data']
                del request.session['otp']
                
                messages.success(request, 'Registration successful!')
                return redirect('Login')  # Redirect to home or login page after successful registration
            else:
                messages.error(request, 'Registration data not found. Please try again.')
                return redirect('SellerReg')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
            return redirect('SellerReg')  # Redirect to registration page if OTP is incorrect

    return render(request, 'Users/seller_send_otp_email.html')
@login_required
def Seller_Details(request, state_id):
    state = get_object_or_404(State, id=state_id)
    if request.method == 'POST':
        farmname = request.POST.get('farm_name')
        street = request.POST.get('landmark')  
        city = request.POST.get('Your_city')
        zipcode = request.POST.get('your_pin')
        print(farmname)
        print(street)
        print(city)
        print(zipcode)
        if farmname and street and city and zipcode:
            print('success')
            try:
                SellerDetails.objects.create(
                    user=request.user,
                    FarmName=farmname,
                    FarmAddress=street,
                    Farmcity=city,
                    Farmzip_code=zipcode,
                    state=state
                )
                return redirect('SellerHome')
            except IntegrityError as e:
                print(f"IntegrityError: {e}")
                error_message = "There was an error saving your address. Please try again."
        else:
            error_message = "All fields (farm name, street, city, and zipcode) are required."
        
        context={
            'error': error_message,
            'state_id': state_id,
            'state':state
        }
    else:
        context={
            'state_id': state_id,
            'state':state
        }

    return render(request, 'Users/Sellerentry.html', context)
@never_cache
def adminlog(request):
    if request.user.is_authenticated and request.user.is_staff:
        username = request.user.username
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=30)
        
        # Data for the new sales chart (last 30 days)
        sales_data = Order.objects.filter(order_date__date__range=[start_date, end_date])\
            .annotate(date=TruncDate('order_date'))\
            .values('date')\
            .annotate(total_sales=Sum('total_amount'))\
            .order_by('date')

        dates = [item['date'].strftime('%Y-%m-%d') for item in sales_data]
        sales = [float(item['total_sales']) for item in sales_data]
        
        # Data for the existing chart (monthly data for the current year)
        current_year = timezone.now().year
        monthly_data = Order.objects.filter(order_date__year=current_year)\
            .annotate(month=TruncMonth('order_date'))\
            .values('month')\
            .annotate(total_sales=Sum('total_amount'))\
            .order_by('month')

        chart_data = [0] * 12
        for entry in monthly_data:
            month_index = entry['month'].month - 1
            chart_data[month_index] = float(entry['total_sales'])
        
        context = {
            'username': username,
            'sales_dates': json.dumps(dates),
            'sales_amounts': json.dumps(sales),
            'chart_data': json.dumps(chart_data),
        }
        
        return render(request, 'admin/dashboard.html', context)
    else:
        return redirect('Login')



@login_required
def adminupdate(request):
    user = request.user
    if request.method == 'POST':
        try:

            user.username = request.POST.get('username', user.username)
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.phone_number = request.POST.get('phone_number', user.phone_number)
            user.save()
            messages.success(request, "Admin details updated successfully.")
        except Exception as e:
            messages.error(request, f"Failed to update admin details. Error: {str(e)}")
        return redirect('adminupdate')

    context = {
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone_number': user.phone_number,
    }
    return render(request, 'admin/user.html', context)
@login_required
def userslist(request):
    users = User.objects.all()
    return render(request, 'admin/tables.html', {'users': users, 'username': request.user.username})
@login_required
def deactivate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.is_active = False
        user.save()
        messages.success(request, f"User {user.username} has been deactivated successfully.")
        return redirect('adminuserslist')
    users = User.objects.all()
    return render(request, 'admin/tables.html', {'users': users, 'username': request.user.username})
