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
            url_name = form.cleaned_data['url_name']  # Capture URL Name
            project_codes = [code.strip() for code in form.cleaned_data['project_codes'].split(',') if code.strip()]
            project_uuid = str(uuid.uuid4())

            metadata = {
                "uuid": project_uuid,
                "authors": authors,
                "projectName": project_name,
                "Description": description,
                "url_name": url_name,  # Store URL Name in metadata
                "license": {
                    "so:name": "toronto",
                    "so:url": "https://www.nature.com/articles/461168a#Sec2"
                },
                "project_codes": project_codes,
                "so:url": f"https://opendata.earlham.ac.uk/wheat/under_license/toronto/{url_name}/",
                "irods_path": f"/grassrootsZone/public/under_license/toronto/{url_name}",
                "@type": "Grassroots:Project",
                "type_description": "Dataset",
                "so:image": "https://grassroots.tools/grassroots/images/aiss/drawer"
            }

            # Custom fields handling (not added to JSON yet)
            custom_fields = {}
            for key, value in request.POST.items():
                if key.startswith('custom_field_') and value:
                    field_num = key.split('_')[-1]
                    custom_value_key = f'custom_value_{field_num}'
                    if custom_value_key in request.POST:
                        custom_fields[value] = request.POST[custom_value_key]


            # Save metadata to session for review
            request.session['metadata'] = metadata
            request.session['custom_fields'] = custom_fields

            return redirect('review_metadata')
    else:
        form = MetadataForm()

    return render(request, 'form_opendata.html', {'form': form})



def review_metadata(request):
    metadata = request.session.get('metadata')
    custom_fields = request.session.get('custom_fields', {})
    
    if not metadata:
        return redirect('form_opendata')

    if request.method == 'POST':
        form = MetadataForm(request.POST)
        if form.is_valid():
            # Clean and strip whitespace, and filter out empty items
            cleaned_authors = [author.strip() for author in form.cleaned_data['authors'].split(',') if author.strip()]
            cleaned_project_codes = [code.strip() for code in form.cleaned_data['project_codes'].split(',') if code.strip()]
            cleaned_description = form.cleaned_data['description'].replace('\r\n', ' ').replace('\n', ' ').strip()
            url_name = form.cleaned_data['url_name'].strip()

            # Update the session with the cleaned data, keeping the original structure intact
            metadata.update({
                'projectName': form.cleaned_data['project_name'],
                'url_name': url_name,  # Update URL name in metadata
                'authors': cleaned_authors,
                'Description': cleaned_description,
                'project_codes': cleaned_project_codes,
                # Update the URLs with the new url_name value
                'so:url': f"https://opendata.earlham.ac.uk/wheat/under_license/toronto/{url_name}/",
                'irods_path': f"/grassrootsZone/public/under_license/toronto/{url_name}",
            })

            # Save the updated metadata back to the session
            request.session['metadata'] = metadata

            # Update custom fields in the session
            custom_fields_updated = {}
            for key, value in request.POST.items():
                if key.startswith('custom_field_') and value:
                    field_num = key.split('_')[-1]
                    custom_value_key = f'custom_value_{field_num}'
                    if custom_value_key in request.POST:
                        custom_fields_updated[value] = request.POST[custom_value_key]
            request.session['custom_fields'] = custom_fields_updated
            
            return redirect('submit_metadata')
    else:
        # Prepopulate the form with current metadata
        form = MetadataForm(initial={
            'project_name': metadata.get('projectName', ''),
            'url_name': metadata.get('url_name', ''),
            'authors': ', '.join(metadata.get('authors', [])),
            'description': metadata.get('Description', ''),
            'project_codes': ', '.join(metadata.get('project_codes', [])),
        })

    return render(request, 'review_metadata.html', {'form': form, 'custom_fields': custom_fields})







def submit_metadata(request):
    metadata = request.session.get('metadata')
    if not metadata:
        return redirect('form_opendata')

    # Clean up any remaining whitespace
    metadata['authors'] = [author.strip() for author in metadata['authors']]
    metadata['project_codes'] = [code.strip() for code in metadata['project_codes']]
    metadata['Description'] = metadata['Description'].replace('\r\n', ' ').replace('\n', ' ').strip()

    # Remove the url_name from the final metadata
    url_name = metadata.pop('url_name', None)
    project_name = metadata['projectName']
    sanitized_url_name = url_name.replace(' ', '_') if url_name else project_name.replace(' ', '_')

    # Save JSON file using url_name instead of project_name
    json_path = os.path.join(settings.BASE_DIR, 'form_opendata', f'{sanitized_url_name}.json')
    with open(json_path, 'w') as json_file:
        json.dump(metadata, json_file, indent=4)

    del request.session['metadata']

    json_url = os.path.join('/form_opendata', f'{sanitized_url_name}.json')
    view_json_url = reverse('view_json', args=[sanitized_url_name])

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