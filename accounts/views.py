from django.contrib import messages, auth

from django.contrib.auth.decorators import login_required

from django.core.urlresolvers import reverse

from django.shortcuts import render, redirect

from django.template.context_processors import csrf

from accounts.forms import UserRegistrationForm, UserLoginForm

from django.views.decorators.csrf import csrf_exempt

import datetime

from django.conf import settings

import stripe

import arrow

import json

from accounts.models import User

from django.http import HttpResponse


# Create your views here.5

stripe.api_key = settings.STRIPE_SECRET

def register(request):

    if request.method == 'POST':

        form = UserRegistrationForm(request.POST)

        if form.is_valid():

            try:

                customer = stripe.Customer.create(

                    email = form.cleaned_data['email'],

                    card = form.cleaned_data['stripe_id'],

                    plan = 'REG_MONTHLY',

                )

            except stripe.error.CardError, e:

                messages.error(request, "Your card was declined!")


            if customer:

                user = form.save()

                user.stripe_id = customer.id

                user.subscription_end = arrow.now().replace(weeks=+4).datetime

                user.save()

                if user:

                    auth.login(request, user)

                    messages.success(request, "You have sucessfully registered")

                    return redirect(reverse('profile'))

                else:

                    messages.error(request, "unable to log you in at this time!")

            else:

                messages.error(request, "We were unable to take a payment with that card!")

    else:

        today = datetime.date.today()

        form = UserRegistrationForm(initial={'expiry_month': today.month,
                                             'expiry_year': today.year})

    args = {'form': form, 'publishable': settings.STRIPE_PUBLISHABLE}

    args.update(csrf(request))

    return render(request, 'register.html', args)


def login(request, success_url=None):

    if request.method == 'POST':

        form = UserLoginForm(request.POST)

        if form.is_valid():

            user = auth.authenticate(email=request.POST.get('email'), password=request.POST.get('password'))

            if user is not None:

                auth.login(request, user)

                messages.error(request, "You have sucessfully logged in")

                return redirect(reverse('profile'))

            else:

                form.add_error(None, "Your email or password was not recognised")

    else:

        form = UserLoginForm()

    args = {'form':form}

    args.update(csrf(request))

    return render(request, 'login.html', args)


@login_required(login_url='/accounts/login/')

def profile(request):

    return render(request, "profile.html")

def logout(request):

    auth.logout(request)

    messages.success(request, "You have successfully logged out")

    return render(request, 'index.html')

@login_required(login_url='/accounts/login/')

def cancel_subscriptions(request):

    try:

        customer = stripe.Customer.retrieve(request.user.stripe_id)

        customer.cancel_subscription(at_period_end=True)

    except Exception, e:

        messages.error(request, e)

    return redirect('profile')


@csrf_exempt
def subscriptions_webhook(request):

    event_json = json.loads(request.body)

    # Verify the event by fetching it from Stripe

    try:

        # firstly verify this is a real event generated by Stripe.com

        event = stripe.Event.retrieve(event_json["id"])

        # get our user

        user = User.objects.get(stripe_id=event_json["customer"])

        if user and event_json['type'] == "invoice.payment_succeeded":

            user.subscription_end = arrow.now().replace(weeks=+4).datetime

            user.save()

    except stripe.InvalidRequestError, e:

        return HttpResponse(status=404)

    return HttpResponse(status=200)









