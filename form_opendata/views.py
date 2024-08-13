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

    if request.method == 'POST':
        form = MetadataForm(request.POST)
        if form.is_valid():
            # Clean and strip whitespace from authors and project codes
            cleaned_authors = [author.strip() for author in form.cleaned_data['authors'].split(',')]
            cleaned_project_codes = [code.strip() for code in form.cleaned_data['project_codes'].split(',')]

            # Update the session with the cleaned data
            request.session['metadata'] = {
                'projectName': form.cleaned_data['project_name'],
                'authors': cleaned_authors,
                'Description': form.cleaned_data['description'],
                'project_codes': cleaned_project_codes,
            }
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
    # Retrieve metadata from session
    metadata = request.session.get('metadata')
    if not metadata:
        return redirect('form_opendata')

     # Clean up any remaining whitespace in the session data
    metadata['authors'] = [author.strip() for author in metadata['authors']]
    metadata['project_codes'] = [code.strip() for code in metadata['project_codes']]
    
    # Extract project name from the metadata
    project_name = metadata['projectName']

    # Define the path to save the JSON file
    json_path = os.path.join(settings.BASE_DIR, 'form_opendata', f'{project_name}.json')

    # Write the metadata to the JSON file
    with open(json_path, 'w') as json_file:
        json.dump(metadata, json_file, indent=4)

    # Optionally clear the session data after saving
    del request.session['metadata']

    # Return a simple success response
    return HttpResponse("Metadata captured and processed successfully!")


