from django.contrib import messages
from django.shortcuts import redirect


class AuditTrailMixin:
    def form_valid(self, form):
        if not form.instance.pk:
            form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user

        if form.instance.pk:
            current_obj = self.model.objects.filter(pk=form.instance.pk).first()
            if current_obj and not current_obj.is_active:
                messages.error(self.request, f"Error: This {self.model.__name__} is archived.")
                return redirect(self.success_url)
        return super().form_valid(form)
