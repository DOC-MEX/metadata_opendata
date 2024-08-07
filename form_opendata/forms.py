from django import forms

class MetadataForm(forms.Form):
    authors = forms.CharField(widget=forms.Textarea, help_text="Enter authors separated by commas")
    project_name = forms.CharField(max_length=100)
    description = forms.CharField(widget=forms.Textarea)
    project_codes = forms.CharField(widget=forms.Textarea, help_text="Enter project codes separated by commas")
