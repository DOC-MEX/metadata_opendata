from django import forms

class MetadataForm(forms.Form):
   project_name = forms.CharField(max_length=100, required=True, label="Project Name", initial="")
   authors = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=True, label="Authors", help_text="Enter authors separated by commas", initial="")
   description = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}), required=True, label="Description", initial="")
   project_codes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label="Project Codes", help_text="Enter project codes separated by commas", initial="")
