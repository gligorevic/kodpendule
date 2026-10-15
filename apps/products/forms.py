from django import forms
from django.utils.translation import gettext_lazy as _

from apps.products.services.inventory_xml import MAX_XML_BYTES


class InventoryXMLUploadForm(forms.Form):
    xml_file = forms.FileField(
        label=_("Inventory XML"),
        help_text=_("StanjeArtikalaWeb XML, up to 5 MB, UTF-8 or Windows-1250."),
        widget=forms.ClearableFileInput(attrs={"accept": ".xml,application/xml,text/xml"}),
    )

    def clean_xml_file(self):
        upload = self.cleaned_data["xml_file"]
        if upload.size > MAX_XML_BYTES or not upload.size:
            raise forms.ValidationError(_("Upload a non-empty XML file up to 5 MB."))
        return upload


class InventoryCategoryForm(forms.Form):
    def __init__(self, *args, rows, categories, selected, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", _("Choose a category")), *categories]
        for row in rows:
            if row["action"] == "new":
                self.fields[f"category_{row['line']}"] = forms.ChoiceField(
                    label=row["name"], choices=choices, required=False,
                    initial=selected.get(row["sku"], ""),
                )
