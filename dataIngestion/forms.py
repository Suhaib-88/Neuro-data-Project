from django import forms
from .models import upload_Dataset

class DatasetDetails(forms.ModelForm):
    class Meta:
        model= upload_Dataset
        fields = '__all__'
        exclude = ['user','problem_ID','user_id','import_data','file_from_resources']
        widgets= {
        'problem_statement_type':forms.Select(attrs={'class':'form-select'}),
        'problem_statement_name':forms.TextInput(attrs={'class':'form-control'}),
        'problem_statement_description': forms.Textarea(attrs={'class':'form-control'}),
        }        