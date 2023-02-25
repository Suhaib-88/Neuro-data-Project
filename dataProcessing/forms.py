from django.forms import ModelForm,Select
from .models import exportDataModel


class exportDataForm(ModelForm):
    class Meta:
        model=exportDataModel
        fields="__all__"
        widgets= {
        'export_data_source':Select(attrs={'class':'form-select'}),
        "file_type":Select(attrs={'class':'form-select'})}