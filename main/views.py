from django.http import JsonResponse
from django.shortcuts import render, redirect,HttpResponse
from django.views.decorators.csrf import csrf_protect,csrf_exempt
from firestoreconfig import db,bucket,google_credentials,firebase_config
import magic
import os
from dotenv import load_dotenv
import razorpay
load_dotenv()
import json
from google.cloud import aiplatform

from vertexai.language_models import TextGenerationModel
PROJECT_ID = 'resume-builder-69ce7'
import vertexai
REGION = 'us-central1'

RAZORPAY_API_KEY = os.getenv('RAZORPAY_API_KEY')
RAZORPAY_API_SECRET = os.getenv('RAZORPAY_API_SECRET')
client = razorpay.Client(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET))


def home(request):
    return render(request,'main/index.html')

def header(request):
    return render(request,'main/header.html')

@csrf_protect
def create_cv(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        contact_info = request.POST.get('contact_info')
        email_web = request.POST.get('email_web')
        website = request.POST.get('website')
        profession = request.POST.get('profession')
        profile_descrition = request.POST.get('profile_text')
        profile_photo = request.FILES.get('profile_photo')
        phone = request.POST.get('phone')
        languages_known = request.POST.get('languages_known').split(',')
        skills = request.POST.get('skills').split(',')

        if profession:
            profession = profession.upper()

        experiences = []
        for key in request.POST:
            if key.startswith('experiences['):
                index = key.split('[')[1].split(']')[0]
                if index.isdigit():
                    index = int(index)
                    while len(experiences) <= index:
                        experiences.append({})
                    experiences[index][key.split('][')[1].split(']')[0]] = request.POST[key]

        educations = []
        for key in request.POST:
            if key.startswith('educations['):
                index = key.split('[')[1].split(']')[0]
                if index.isdigit():
                    index = int(index)
                    while len(educations) <= index:
                        educations.append({})
                    educations[index][key.split('][')[1].split(']')[0]] = request.POST[key]

        resume_ref = db.collection('resumes').document()
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(profile_photo.read())
        profile_photo.seek(0)

        blob = bucket.blob(f'profile_photos/{profile_photo.name}')
        blob.upload_from_file(profile_photo, content_type=mime_type)

        resume_data = {
            'first_name': first_name.upper(),
            'last_name': last_name.upper(),
            'contact_info': contact_info,
            'email_web': email_web,
            'website': website,
            'profession': profession,
            'profile_description':profile_descrition,
            'profile_photo': blob.public_url,
            'languages_known': languages_known,
            'phone': phone,
            'skills': skills,
            'education': educations,
            'experience': experiences,
            'payment_status':False,
        }

        resume_ref.set(resume_data)

        resume_id = resume_ref.id

        return redirect('resume_preview', resume_id = resume_id)
    return render(request,'main/index.html')


def resume_preview(request, resume_id):
    resume_ref = db.collection('resumes').document(resume_id)
    if resume_ref.get().exists:
        resume_details = resume_ref.get().to_dict()
        resume_details['id'] = resume_id
        amount = int(os.getenv('AMOUNT'))
        order_id = initiate_payment(amount)
        context = {
            'order_id': order_id,
            'amount': amount,
            'resume' : resume_details,
            'RAZORPAY_API_KEY':os.getenv('RAZORPAY_API_KEY')
        }
        return render(request, 'main/resume_preview.html', context)
    
    return HttpResponse('Something went wrong.Try Again Later')

@csrf_exempt
def payment_process(request):
    if request.method == "POST":
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)
        resume_id = body_data.get('resume_id')

        resume_ref = db.collection('resumes').document(resume_id)
        params_dict = body_data.get('response1')

        try:
            status = client.utility.verify_payment_signature(params_dict)
            if status:
                if resume_ref.get().exists:
                    resume_ref.update({
                        'payment_status':True,
                        'payment_id':params_dict.get('razorpay_payment_id')
                })
                return JsonResponse({
                    'status':'true',
                    'resume_id':resume_id
                })
            else:
                return JsonResponse({
                    'status':'false',
                    'resume_id':resume_id,
                    'payment_id':params_dict.get('razorpay_payment_id'),
                })
        except:
            return JsonResponse({
                    'status':'failed',
                    'resume_id':resume_id
            })
    else:
        return JsonResponse({
                    'status':'failed',
                    'resume_id':resume_id
        })

def initiate_payment(amount, currency='INR'):
    data = {
        'amount': amount * 100,
        'currency': currency,
        'payment_capture': '1'
    }
    response = client.order.create(data=data)
    return response['id']


def payment_success(request, resume_id):
    resume_ref = db.collection('resumes').document(resume_id)
    resume_details = resume_ref.get().to_dict()
    return render(request, 'main/resume_download.html', {'resume': resume_details})
    

def payment_failed(request):
    return render(request, 'main/payment_failed.html')


def getPrompt(form_data):
    input_text = form_data.get('profile_text', '')
    first_name = form_data.get('first_name', '')
    last_name = form_data.get('last_name', '')
    profession = form_data.get('profession', '')
    email = form_data.get('email_web', '')
    website = form_data.get('website', '')
    languages_known = form_data.get('languages_known', '')
    phone = form_data.get('phone', '')
    skills = form_data.get('skills', '')
    input_text = form_data.get('input_text')

    experiences = []
    for key in form_data:
        if key.startswith('experiences['):
            index = key.split('[')[1].split(']')[0]
            if index.isdigit():
                index = int(index)
                while len(experiences) <= index:
                    experiences.append({})
                experiences[index][key.split('][')[1].split(']')[0]] = form_data[key]

    educations = []
    for key in form_data:
        if key.startswith('educations['):
            index = key.split('[')[1].split(']')[0]
            if index.isdigit():
                index = int(index)
                while len(educations) <= index:
                    educations.append({})
                educations[index][key.split('][')[1].split(']')[0]] = form_data[key]

    experience_text = ""
    for exp in experiences:
        experience_text += f"{first_name} have experience as a {exp['job_title']} at {exp['company']} company in ({exp['year']}), "

    education_text = ""
    for edu in educations:
        education_text += f" {first_name} holds a {edu['degree']} degree from {edu['institution']} ({edu['year']}), "

    prompt = f"""
    Create a 4-5 sentence bio for the user with the following info. Highlight his skills and experience:
    Name: {first_name} {last_name}
    Profession: {profession}
    About: '{input_text}'
    Languages Known: {languages_known}
    Skills: {skills}
    Educations: {education_text.strip(', ')}
    Experiences: {experience_text.strip(', ')}
    Note: The experiences field may be empty. If so, focus more on skills and education.
    """
    return prompt

def enhance_text(request):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)

        prompt = getPrompt(body_data)

        aiplatform.init(credentials=google_credentials)
        vertexai.init(project = PROJECT_ID, location = REGION, credentials = google_credentials)

        generation_model = TextGenerationModel.from_pretrained("text-bison@001")
        enhancedText = generation_model.predict(prompt=prompt).text

        return JsonResponse({
            'enhanced_text':enhancedText,
        })