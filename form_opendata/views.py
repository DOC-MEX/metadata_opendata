import os
import json
import uuid
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import MetadataForm
from django.conf import settings

# Create your views here.
#def form_opendata(request):
#    return render(request, 'form_opendata.html')


def form_opendata(request):
    if request.method == 'POST':
        form = MetadataForm(request.POST)
        if form.is_valid():
            authors = [author.strip() for author in form.cleaned_data['authors'].split(',')]
            project_name = form.cleaned_data['project_name']
            description = form.cleaned_data['description']
            project_codes = [code.strip() for code in form.cleaned_data['project_codes'].split(',')]
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
    return render(request, 'review_metadata.html', {'metadata': metadata})

def submit_metadata(request):
    metadata = request.session.get('metadata')
    if not metadata:
        return redirect('form_opendata')

    project_name = metadata['projectName']

    # Save JSON file in the form_opendata directory
    json_path = os.path.join(settings.BASE_DIR, 'form_opendata', f'{project_name}.json')
    #json_path = settings.BASE_DIR / 'form_opendata' / f'{project_name}.json'
    with open(json_path, 'w') as json_file:
        json.dump(metadata, json_file, indent=4)

    # Add metadata to iRODS
    #os.system(f'imeta add -C /grassrootsZone/public/under_license/toronto/{project_name} license Toronto')
    #os.system(f'imeta add -C /grassrootsZone/public/under_license/toronto/{project_name} license_url "https://www.nature.com/articles/461168a#Sec2"')
    #os.system(f'imeta add -C /grassrootsZone/public/under_license/toronto/{project_name} uuid {metadata["uuid"]}')
    #os.system(f'imeta add -C /grassrootsZone/public/under_license/toronto/{project_name} authors "{','.join(metadata["authors"])}"')
    #os.system(f'imeta add -C /grassrootsZone/public/under_license/toronto/{project_name} projectName "{project_name}"')
    #os.system(f'imeta add -C /grassrootsZone/public/under_license/toronto/{project_name} description "{metadata["Description"]}"')

    # Clear the session data
    del request.session['metadata']

    return HttpResponse("Metadata captured and processed successfully!")


