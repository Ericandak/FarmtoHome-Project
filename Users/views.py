
# Create your views here.
from django.shortcuts import render,redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import pyotp
from django.core.mail import send_mail
import random
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_log,logout
from  django.contrib.auth.hashers import make_password
from .models import Address_table,State

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
            'role':'CUSTOMER'
        }
        reg=request.session.get('registration_data')
        email=reg['email']
        if User.objects.filter(email=email).exists():
            error_message = "Email is already registered."
            return render(request, 'Users/Registration.html', {'error_message': error_message})
        else:
        # Redirect to send OTP email
            return redirect('send_otp_email')

    return render(request, 'Users/Registration.html')
    


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
                hashed_password = make_password(registration_data['password'])
                # Assuming you have a model named `User` for user registration
                new_user = User.objects.create(
                    username=username,
                    first_name=registration_data['first_name'],
                    last_name=registration_data['last_name'],
                    email=registration_data['email'],
                    phone_number=registration_data['phone'],
                    password=hashed_password,
                    role=registration_data['role']
                )
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
        print(user)
        if user is not None:
            auth_log(request, user)
            try:
                address = Address_table.objects.get(user=user)
                if address.state is None:
                    # Redirect to state entry page if state is not given
                    return redirect('stateentry')
                elif not address.address or not address.city or not address.zip_code:
                    # Redirect to address entry page if address details are not complete
                    return redirect('enter_address')
                else:
                    # Redirect to home if both state and address details are provided
                    return redirect('home')
            except Address_table.DoesNotExist:
                # Redirect to state entry page if no address record exists
                return redirect('stateentry')
        else:
            error_message = "Username Or password is Wrong."
            return render(request,'Users/Login.html',{'error':error_message})
    return render(request, 'Users/Login.html')
@login_required
def auth_logout(request):
    logout(request)
    return redirect('Login')
@login_required
def home(request):
    return render(request, 'Products/index.html')

@login_required
def stateentry(request):
    if request.method == 'POST':
        state_name = request.POST.get('state')
        country_name = request.POST.get('country')
        
        if state_name and country_name:
            state, created = state.objects.get_or_create(name=state_name, country=country_name)
            address, created = Address_table.objects.get_or_create(user=request.user)
            address.state = state
            address.save()
            return redirect('enter_address')
        else:
            error_message = "Both state and country are required."
            return render(request, 'Users/EnterState.html', {'error': error_message})
    
    return render(request, 'Users/Stateentry.html')

