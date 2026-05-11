from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView
from .models import SamplingPlan, Sample, AnalyticalMethod
from .forms import SamplingPlanForm, SampleForm, AnalyticalMethodForm # Import des formulaires
from production.views import AuditTrailMixin

# ==========================================
# ANALYTICAL METHODS
# ==========================================
class MethodListView(ListView):
    model = AnalyticalMethod
    template_name = 'sampling/method_list.html'
    context_object_name = 'methods'

class MethodCreateView(AuditTrailMixin, CreateView):
    model = AnalyticalMethod
    form_class = AnalyticalMethodForm # Utilisation du Form spécifique
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('sampling:method_list')

# ==========================================
# SAMPLING PLANS
# ==========================================
class PlanListView(ListView):
    model = SamplingPlan
    template_name = 'sampling/plan_list.html'
    context_object_name = 'plans'

class PlanCreateView(AuditTrailMixin, CreateView):
    model = SamplingPlan
    form_class = SamplingPlanForm # Utilisation du Form pour les checkboxes
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('sampling:plan_list')

class PlanManageView(ListView):
    model = Sample
    template_name = 'sampling/plan_manage.html'
    context_object_name = 'entries'

    def get_queryset(self):
        return Sample.objects.filter(sample_plan_id=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plan'] = get_object_or_404(SamplingPlan, pk=self.kwargs['pk'])
        # C'est cette ligne qui manquait pour afficher les champs dans le template :
        context['form'] = SampleForm()
        return context

class SampleCreateView(AuditTrailMixin, CreateView):
    model = Sample
    form_class = SampleForm # Utilisation du Form pour le style Bootstrap
    template_name = 'sampling/plan_manage.html'

    def form_valid(self, form):
        # On lie l'échantillon au plan parent via l'URL
        form.instance.sample_plan = get_object_or_404(SamplingPlan, pk=self.kwargs['plan_pk'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('sampling:plan_manage', kwargs={'pk': self.kwargs['plan_pk']})

class SampleDeleteView(DeleteView):
    model = Sample
    def get_success_url(self):
        # Retour au management du plan après suppression
        return reverse_lazy('sampling:plan_manage', kwargs={'pk': self.object.sample_plan.pk})