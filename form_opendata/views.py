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
    custom_fields = request.session.get('custom_fields', {})
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

    # Sanitize custom field names (replace spaces with underscores)
    sanitized_custom_fields = {key.replace(' ', '_'): value for key, value in custom_fields.items()}

    #merge custom fields into metadata
    metadata.update(sanitized_custom_fields)

    # Save JSON file using url_name instead of project_name
    json_output_path = os.path.join(settings.JSON_OUTPUT_DIR, f'{sanitized_url_name}.json')
    
    # Ensure the JSON_OUTPUT folder exists
    if not os.path.exists(settings.JSON_OUTPUT_DIR):
        os.makedirs(settings.JSON_OUTPUT_DIR)

    # Save JSON file in the JSON_OUTPUT folder
    with open(json_output_path, 'w') as json_file:
        json.dump(metadata, json_file, indent=4)

    #generate and save the Python script to apply metadata to iRODS
    python_script_output_path = os.path.join(settings.JSON_OUTPUT_DIR, f'{sanitized_url_name}_irods_script.py')
    python_script_content = generate_irods_script(metadata)
    with open(python_script_output_path, 'w') as python_script_file:
        python_script_file.write(python_script_content)


    del request.session['metadata']
    del request.session['custom_fields']

    # Since the JSON_OUTPUT directory is not accessible via a direct URL, we'll use the 'serve_json_file' view to serve the file
    json_url = reverse('serve_json_file', args=[sanitized_url_name])
    view_json_url = reverse('view_json', args=[sanitized_url_name])

    return render(request, 'submitted.html', {'json_url': json_url, 'view_json_url': view_json_url})



def view_json(request, filename):
    # Construct the path to the JSON file in JSON_OUTPUT directory
    json_path = os.path.join(settings.JSON_OUTPUT_DIR, f'{filename}.json')
    
    # Check if the file exists
    if not os.path.exists(json_path):
        raise Http404("JSON file not found")

    # Generate the URL to fetch the JSON using serve_json_file
    json_url = reverse('serve_json_file', args=[filename])

    return render(request, 'view_json.html', {'json_url': json_url})


def serve_json_file(request, filename):
    json_path = os.path.join(settings.JSON_OUTPUT_DIR, f'{filename}.json')

    if not os.path.exists(json_path):
        raise Http404("JSON file not found")

    try:
        with open(json_path, 'r') as json_file:
            data = json.load(json_file)
    except json.JSONDecodeError:
        raise Http404("Error decoding JSON file")

    return JsonResponse(data)


def generate_irods_script(metadata):
    # Extract required fields from metadata
    uuid = metadata['uuid']
    authors = ', '.join(metadata['authors'])
    description = metadata['Description']
    license_name = metadata['license']['so:name'].capitalize()
    license_url = metadata['license']['so:url']
    project_name = metadata['projectName']
    irods_path = metadata['irods_path']

    # Generate the Python script content
    script_content = f"""
import json
from irods.session import iRODSSession
from irods.meta import iRODSMeta
from irods.exception import CollectionDoesNotExist

# iRODS connection parameters
IRODS_HOST = 'opendata-dsw'
IRODS_PORT = 1247
IRODS_USER = 'grassroots'
IRODS_PASS = '<removed>'
IRODS_ZONE = 'grassrootsZone'

# Target iRODS collection path
target_collection_path = "{irods_path}"

def apply_metadata(path, metadata, session):
    # Extract and add the specific metadata attributes
    attributes = [
        ('authors', "{authors}"),
        ('description', "{description}"),
        ('license', "{license_name}"),
        ('license_url', "{license_url}"),
        ('projectName', "{project_name}"),
        ('uuid', "{uuid}")
    ]

    try:
        coll = session.collections.get(path)
        for attribute, value in attributes:
            if value:  # Only add metadata if the value is not empty
                meta = iRODSMeta(attribute, value)
                coll.metadata.add(meta)
                print(f"Added metadata: {{attribute}} = {{value}}")
    except CollectionDoesNotExist:
        print(f"Collection does not exist: {{path}}")

# Establish iRODS session
with iRODSSession(host=IRODS_HOST, port=IRODS_PORT, user=IRODS_USER, password=IRODS_PASS, zone=IRODS_ZONE) as session:
    apply_metadata(target_collection_path, metadata, session)
    """
    return script_content