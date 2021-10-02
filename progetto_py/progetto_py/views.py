import os.path

import boto3
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from pymongo import MongoClient

from .forms import *
from .models import *
from .utils import *

client = MongoClient('localhost:27017')
db = client['parkinglots']
col_park = db['parking']

aws_access_key_id = ''
aws_secret_access_key = ''


def signup(request):
    form = SignUpForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('accounts/login')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


@login_required
def home_redirect(request):
    response = redirect('/dashboard/')
    return response

@login_required
def dashboard(request):

    """answer_data = prepare_data_for_answer()
    t.send_message(answer_data)"""
    parks = Park.objects.all()
    parks_str = ""
    # Create a string with all the parks name divided by /
    for park in parks:
        parks_str = parks_str + "/" + park.name
        print(parks_str)
    return render(request, "dashboard.html", {'parks': parks_str[1:], 'parks_arr': parks})


@login_required
def park(request, name):
    return render(request, "single_park_info.html", {'park_name': name})


@login_required
def add_park(request):
    if request.method == 'GET':
        form = FormThingCreation()
        return render(request, "add_park.html", {"form": form})
    elif request.method == 'POST':
        form = FormThingCreation(request.POST)
        if form.is_valid():
            thing_name = form.cleaned_data['name_park']
            # Create new Park model
            new_park = Park(name=thing_name)
            # Add park mongodb
            park_dict = {"_id": thing_name}
            col_park.insert_one(park_dict)
            client = boto3.client(
                'iot', region_name='us-west-2',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )
            client.create_thing(
                thingName=thing_name,
            )
            new_park.save()
            response = client.create_keys_and_certificate(
                setAsActive=True
            )
            keyPair = response["keyPair"]
            certificateArn = response["certificateArn"]
            client.attach_thing_principal(
                thingName=thing_name,
                principal=certificateArn
            )
            client.attach_principal_policy(
                policyName='esit-obj1',
                principal=certificateArn
            )

            filepath = os.path.join('certificates', thing_name + '.txt')
            path = "certificates/" + thing_name
            if not os.path.exists(path):
                os.mkdir(path)
            pemPath = os.path.join('certificates/' + thing_name, 'Thing-certificate.pem.crt')
            privatePath = os.path.join('certificates/' + thing_name, 'Private-private.pem.key')
            if not os.path.exists('certificates'):
                os.makedirs('certificates')
            with open(pemPath, 'w') as f:
                f.write(response["certificatePem"])
            with open(privatePath, 'w') as f:
                f.write(keyPair["PrivateKey"])

            with open(filepath, 'w') as f:
                f.write("Nome Parcheggio:\n" + thing_name)
                f.write("\n")
                f.write("certificatePem:\n" + response["certificatePem"] + "\n")
                f.write("PrivateKey:\n" + keyPair["PrivateKey"] + "\n")
                f.write("certificateId:\n" + response["certificateId"] + "\n")
            final_response = redirect('/dashboard/')
            return final_response


# AGGIUNGERE ELIMINAZIONE FILE CONTENENTE LE INFORMAZIONI DELL'OGGETTO DA ELIMINARE
@login_required
def remove_park(request):
    if request.method == 'GET':
        parks = Park.objects.all()

        return render(request, "remove_park.html", {'parks': parks})
    elif request.method == 'POST':
        form = request.POST.getlist('parkings')
        if form:
            for p in form:
                Park.objects.filter(name=p).delete()
                client = boto3.client(
                    'iot', region_name='us-west-2',
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                )
                response = client.list_thing_principals(
                    thingName=p
                )
                principals = response['principals'][0].split('cert/')
                print(principals[1])

                client.update_certificate(
                    certificateId=principals[1],
                    newStatus='INACTIVE'
                )
                client.detach_thing_principal(
                    thingName=p,
                    principal=response['principals'][0]
                )
                client.detach_policy(
                    policyName='esit-obj1',
                    target=response['principals'][0]
                )
                client.delete_certificate(
                    certificateId=principals[1]
                )

                client.delete_thing(
                    thingName=p
                )
                filepath = os.path.join('certificates', p + '.txt')
                if os.path.exists(filepath):
                    os.remove(filepath)
                else:
                    print("Il file non esiste")
                final_response = redirect('/dashboard/')
                park_dict = {"_id": p}
                col_park.delete_one(park_dict)
            return final_response
        else:
            parks = Park.objects.all()
            err = [{'message': 'Nessun parcheggio inserito', 'code': ''}]
            return render(request, "remove_park.html", {'parks': parks, 'error': err})
