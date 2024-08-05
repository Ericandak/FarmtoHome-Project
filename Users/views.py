
# Create your views here.
from django.shortcuts import render,redirect,reverse,get_object_or_404
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
from django.db import IntegrityError
from django.views.decorators.http import require_GET
from django.templatetags.static import static


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
            return render(request, 'Users/Registration.html', {'error_message': error_message})
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
    user=request.user
    if user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        email = request.POST.get('your_email')
        password = request.POST.get('your_password')
        print(email)
        print(password)

        user = authenticate(request,email=email,password=password)
        # Assume you have a UserProfile model)
        
        if user is not None:
            auth_log(request, user)
            request.session['username'] = user.username
            request.session.save()
            print(f"Session set in Login: {request.session.get('username')}")
            roles = user.role.all()
            role_names = roles.values_list('name', flat=True)
            has_customer_role = 'Customer' in role_names
            has_seller_role = 'Seller' in role_names
            if has_customer_role:
                try:
                    address = Address_table.objects.get(user=user)
                    if address.state is None:
                        return redirect('stateentry')
                    elif not address.address or not address.city or not address.zip_code:
                        return redirect('address_entry')
                    else:
                        if has_seller_role:
                            print('hi')
                            return redirect('customer_dashboard_with_seller_link')
                        return redirect('home')
                except Address_table.DoesNotExist:
                    return redirect('stateentry')    
            if has_seller_role:
                try:
                    Sellrep = SellerDetails.objects.get(user=user)
                    if Sellrep.state is None:
                        return redirect('stateentry')
                    elif not Sellrep.address or not Sellrep.city or not Sellrep.zip_code:
                        return redirect('SellerDetails')
                    else:
                        return redirect('SellerHome')
                except SellerDetails.DoesNotExist:
                    return redirect('stateentry')

        else:
            error_message = "Username or password is incorrect."
            return render(request, 'Users/Login.html', {'error': error_message})

    return render(request, 'Users/Login.html')

@login_required
def auth_logout(request):
    logout(request)
    return redirect('Login')
@login_required
def home(request):
    username = request.session.get('username', None)
    if not username:
        return redirect('Login')  
    return render(request, 'Products/index.html', {'username': username})
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
        print(country_name)
        print(state_name)
        
        if state_name and country_name:
            state, created = State.objects.get_or_create(name=state_name, country=country_name)
            roles = user.role.all()  # This will be a queryset of roles

            # Check if the user has any roles and handle accordingly
            if roles:
                # For example, you can use the first role for logic
                user_role = roles.first().name.upper()

                if user_role=='CUSTOMER':
                    return redirect('address_entry', state_id=state.id)
                elif user_role == 'SELLER':
                    return redirect('SellerDetails', state_id=state.id)
            else:
                error_message = "User has no roles assigned."
                countries = State.objects.values_list('country', flat=True).distinct()
                return render(request, 'Users/Stateentry.html', {'error': error_message, 'countries': countries})
        else:
            error_message = "Both state and country are required."
            countries = State.objects.values_list('country', flat=True).distinct()
            return render(request, 'Users/Stateentry.html', {'error': error_message,'countries':countries})
    countries = State.objects.values_list('country', flat=True).distinct()
    return render(request, 'Users/Stateentry.html',{'countries':countries})

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

def profile_update(request):
    username = request.session.get('username', None)
    user=None
    address=None
    if username:
        try:
            user = get_object_or_404(User, username=username)
            address = get_object_or_404(Address_table, user=user)
            state = address.state if address else None
        except (User.DoesNotExist,Address_table.DoesNotExist):
            user = None  # Handle the case where the user does not exist
            address = None
        if request.method == 'POST':
            user.email = request.POST.get('email', user.email)
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.phone_number = request.POST.get('phone_number', user.phone_number)
            user.save()
        
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
        countries = State.objects.exclude(country=state.country).values_list('country', flat=True).distinct()
    return render(request, 'Users/User_profile.html', {'user': user,'address':address,'state':state,'countries':countries})

def SellerProfile(request):
    context = {
        'background_image_url': static('assets/img/crops.jpg')
    }
    return render(request,'Users/SellerLogin.html',context)
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
                    role=seller_role
                )
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
def SellerDetails(request,state_id):
    if request.method == 'POST':
        farmname=request.POST.get('Farm_name')
        street = request.POST.get('Landmark')
        city = request.POST.get('your_city')
        zipcode = request.POST.get('your_pin')
        state = get_object_or_404(State, id=state_id)
        if street and city and zipcode:
            SellerDetails.objects.create(
            user=request.user,
            FarmName=farmname,
            FarmAddress=street,
            Farmcity=city,
            Farmzip=zipcode,
            state=state
        )
        try:
                return redirect('SellerHome')  # Redirect to the home page or another appropriate page
        except IntegrityError as e:
                # Catch and print any IntegrityErrors
                print(f"IntegrityError: {e}")
                error_message = "There was an error saving your address. Please try again."
                return render(request, 'Users/Sellerentry.html', {
                    'error': error_message,
                    'state': state_id
                })
        else:
            error_message = "All fields (street, city, and zipcode) are required."
            return render(request, 'Users/Sellerentry.html', {
                'error': error_message,
                'state': state_id,
                'address': addresss
            })

    return render(request, 'Users/Sellerentry.html', {
        'state': state_id
    })
