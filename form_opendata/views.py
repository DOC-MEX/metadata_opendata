import os
import json
import uuid
from django.shortcuts import render, redirect
from .forms import MetadataForm
from django.conf import settings
from django.http import JsonResponse, Http404
from django.urls import reverse

# Create your views here.
#def form_opendata(request):
#    return render(request, 'form_opendata.html')


def form_opendata(request):
    if request.method == 'POST':
        form = MetadataForm(request.POST)
        if form.is_valid():
            # Clean authors and project codes by removing empty items caused by double commas
            authors = [author.strip() for author in form.cleaned_data['authors'].split(',') if author.strip()]
            project_name = form.cleaned_data['project_name']
            description = form.cleaned_data['description']
            project_codes = [code.strip() for code in form.cleaned_data['project_codes'].split(',') if code.strip()]
            project_uuid = str(uuid.uuid4())
            
            metadata = {
                "uuid": project_uuid,
                "authors": authors,
                "projectName": project_name,
                "Description": description,
                "license": {
                    "so:name": "toronto",
                    "so:url": "https://www.nature.com/articles/461168a#Sec2"
                },
                "project_codes": project_codes,
                "so:url": f"https://opendata.earlham.ac.uk/wheat/under_license/toronto/{project_name}/",
                "irods_path": f"/grassrootsZone/public/under_license/toronto/{project_name}",
                "@type": "Grassroots:Project",
                "type_description": "Dataset",
                "so:image": "https://grassroots.tools/grassroots/images/aiss/drawer"
            }

            # Save metadata to session for review
            request.session['metadata'] = metadata

            return redirect('review_metadata')
    else:
        form = MetadataForm()

    return render(request, 'form_opendata.html', {'form': form})



def review_metadata(request):
    metadata = request.session.get('metadata')
    if not metadata:
        return redirect('form_opendata')

    if request.method == 'POST':
        form = MetadataForm(request.POST)
        if form.is_valid():
            # Clean and strip whitespace, and filter out empty items
            cleaned_authors = [author.strip() for author in form.cleaned_data['authors'].split(',') if author.strip()]
            cleaned_project_codes = [code.strip() for code in form.cleaned_data['project_codes'].split(',') if code.strip()]
            cleaned_description = form.cleaned_data['description'].replace('\r\n', ' ').replace('\n', ' ').strip()

            # Update the session with the cleaned data, keeping the original structure intact
            metadata.update({
                'projectName': form.cleaned_data['project_name'],
                'authors': cleaned_authors,
                'Description': cleaned_description,
                'project_codes': cleaned_project_codes,
            })

            # Save the updated metadata back to the session
            request.session['metadata'] = metadata
            return redirect('submit_metadata')
    else:
        # Prepopulate the form with current metadata
        form = MetadataForm(initial={
            'project_name': metadata.get('projectName', ''),
            'authors': ', '.join(metadata.get('authors', [])),
            'description': metadata.get('Description', ''),
            'project_codes': ', '.join(metadata.get('project_codes', [])),
        })

    return render(request, 'review_metadata.html', {'form': form})



def submit_metadata(request):
    metadata = request.session.get('metadata')
    if not metadata:
        return redirect('form_opendata')

    metadata['authors'] = [author.strip() for author in metadata['authors']]
    metadata['project_codes'] = [code.strip() for code in metadata['project_codes']]
    metadata['Description'] = metadata['Description'].replace('\r\n', ' ').replace('\n', ' ').strip()

    project_name = metadata['projectName']
    sanitized_project_name = project_name.replace(' ', '_')

    json_path = os.path.join(settings.BASE_DIR, 'form_opendata', f'{sanitized_project_name}.json')
    with open(json_path, 'w') as json_file:
        json.dump(metadata, json_file, indent=4)

    del request.session['metadata']

    json_url = os.path.join('/form_opendata', f'{sanitized_project_name}.json')
    view_json_url = reverse('view_json', args=[sanitized_project_name])

    return render(request, 'submitted.html', {'json_url': json_url, 'view_json_url': view_json_url})

def view_json(request, filename):
    # Construct the path to the JSON file
    json_path = os.path.join(settings.BASE_DIR, 'form_opendata', f'{filename}.json')
    
    # Check if the file exists
    if not os.path.exists(json_path):
        raise Http404("JSON file not found")

    # Generate the URL to fetch the JSON using serve_json_file
    json_url = reverse('serve_json_file', args=[filename])
    
    return render(request, 'view_json.html', {'json_url': json_url})


def serve_json_file(request, filename):
    json_path = os.path.join(settings.BASE_DIR, 'form_opendata', f'{filename}.json')

    if not os.path.exists(json_path):
        raise Http404("JSON file not found")

    try:
        with open(json_path, 'r') as json_file:
            data = json.load(json_file)
    except json.JSONDecodeError:
        raise Http404("Error decoding JSON file")

    return JsonResponse(data)