from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from production.models import Process
from .models import Client, Project, MoleculeType, AnalyticalMethod, GlobalUnitOperation
from .forms import ClientForm, ProjectForm, MoleculeTypeForm, AnalyticalMethodForm, GlobalUnitOperationForm
from phf.utils import AuditTrailMixin, StatusResetMixin, GenericDeleteView, GenericRestoreView, EntityDetailView, \
    EntityValidateView, EntityRejectView, FilterStateMixin
from.security import ReferentialRoleRequiredMixin


# ==========================================
# MOLECULE TYPE VIEWS
# ==========================================
class MoleculeTypeListView(ReferentialRoleRequiredMixin, FilterStateMixin, ListView):
    """
    Handles the display of a list of molecule types with filtering and referential role access
    control.

    This class-based view provides a way to display molecule types in a list format with support
    for search functionality. It ensures that only users with appropriate referential roles can
    access this view. The list can be filtered based on predefined search fields, and the view is
    rendered using a specified template.

    Attributes:
        model (Model): The model associated with this view, which is `MoleculeType`.
        template_name (str): The path to the template used for rendering the list view.
        context_object_name (str): The name of the context variable to store the list of
            molecule types for template access.
        search_fields (list[str]): The list of model fields that will be used for filtering
            search results.
    """
    model = MoleculeType
    template_name = 'referential/molecule_type_list.html'
    context_object_name = 'molecule_types'
    search_fields = ['name']

class MoleculeTypeCreateView(ReferentialRoleRequiredMixin, AuditTrailMixin, CreateView):
    """
    View for creating a new MoleculeType.

    Handles the creation of a new MoleculeType instance through a form. This view
    is protected by access restrictions and includes an audit trail for changes.
    It renders a generic form template and redirects to the MoleculeType list
    upon successful submission.

    Attributes:
        model (MoleculeType): The model associated with this view.
        form_class (MoleculeTypeForm): The form class used for creating a
            MoleculeType instance.
        template_name (str): The path to the template used for rendering the form.
        success_url (str): The URL to redirect to upon successful form submission.
    """
    model = MoleculeType
    form_class = MoleculeTypeForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:moleculetype_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add New Molecule Type"
        return context

class MoleculeTypeUpdateView(ReferentialRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    """
    View for updating a MoleculeType instance.

    This class-based view is responsible for handling the update operation for
    MoleculeType model instances. It integrates various mixins to handle
    authentication, logging, and status management functionalities. The view
    renders a form template for editing MoleculeType instances and manages
    success redirection upon completion.

    Attributes:
        model (MoleculeType): The model class associated with the view.
        form_class (MoleculeTypeForm): The form class used for input validation
            and rendering.
        template_name (str): Path to the template used for rendering the form.
        success_url (str): URL to redirect to on successful form submission.
    """
    model = MoleculeType
    form_class = MoleculeTypeForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:moleculetype_list')

class MoleculeTypeDeleteView(ReferentialRoleRequiredMixin, GenericDeleteView):
    """
    Handles the deletion of MoleculeType objects.

    This class provides the functionality to delete a MoleculeType instance from the
    database. It ensures that the user has the required referential role permissions
    to perform the delete operation. After successful deletion, it redirects the user
    to the MoleculeType list view.

    Attributes:
        model: Specifies the model class associated with this view.
        success_url (str): The URL to redirect to after a successful delete operation.
    """
    model = MoleculeType
    success_url = reverse_lazy('referential:moleculetype_list')

class MoleculeTypeRestoreView(ReferentialRoleRequiredMixin, GenericRestoreView):
    """
    Manages restoration of a deleted MoleculeType object.

    This class handles the logic for restoring a deleted MoleculeType entry in the
    system. It ensures that only users with the appropriate referential role can
    access this functionality. The class uses the predefined model and redirect URL
    to handle the restoration process and"""
    model = MoleculeType
    redirect_url = 'referential:moleculetype_list'

class MoleculeTypeDetailView(ReferentialRoleRequiredMixin, EntityDetailView):
    """
    Manages detailed view of a molecule type.

    This class is responsible for providing a detailed view of the MoleculeType
    model within the application. It combines functionality from
    ReferentialRoleRequiredMixin and EntityDetailView to enforce relevant
    permissions and provide the necessary data to the user.

    Attributes:
        model: Specifies the model class associated with the view.
    """
    model = MoleculeType


class MoleculeTypeValidateView(ReferentialRoleRequiredMixin, EntityValidateView):
    """
    Handles the validation of molecule types within the system.

    This class is responsible for managing the validation process for
    MoleculeType instances. It ensures that only authorized users with
    specific roles can perform validation operations by extending functionality
    from ReferentialRoleRequiredMixin and EntityValidateView. It also handles
    redirection after successful validation.

    Attributes:
        model: The model class associated with the view (MoleculeType).
        redirect_url (str): The URL to redirect to after successful validation.
    """
    model = MoleculeType
    redirect_url = 'referential:moleculetype_list'

class MoleculeTypeRejectView(ReferentialRoleRequiredMixin, EntityRejectView):
    """
    Represents a view for rejecting MoleculeType entities with specific role restrictions.

    This class is designed to handle the rejection of instances of the MoleculeType model.
    It enforces user role requirements through the ReferentialRoleRequiredMixin and manages
    redirection after the rejection process is completed.

    Attributes:
        model (Type[Model]): The model class used by this view, which is MoleculeType.
        redirect_url (str): The URL to redirect to after the rejection process is completed.
    """
    model = MoleculeType
    redirect_url = 'referential:moleculetype_list'

# ==========================================
# CLIENT VIEWS
# ==========================================
class ClientListView(ReferentialRoleRequiredMixin, FilterStateMixin, ListView):
    """
    Manages the display and filtering of a list of clients.

    This class is responsible for rendering a list view of client objects, allowing users to
    filter and search through the list based on specified criteria. It utilizes several mixins
    to enforce role-specific access control and manage the state of applied filters.

    Attributes:
        model (Type[Model]): The database model representing the client data.
        template_name (str): The path to the template used to render the client list view.
        context_object_name (str): The name of the context variable containing the list of clients.
        search_fields (list[str]): The fields to be used for searching through the client list.
    """
    model = Client
    template_name = 'referential/client_list.html'
    context_object_name = 'clients'
    search_fields = ['name', 'code']

class ClientCreateView(ReferentialRoleRequiredMixin, AuditTrailMixin, CreateView):
    """
    Handles the creation of new Client objects through a form view.

    This class-based view integrates functionality for role-based access
    control, audit trail logging, and form handling to create new Client
    entries within the system. It relies on the Client model and uses the
    ClientForm form class for user input handling. The template rendered
    for this view is generic_form.html. Upon successful form submission
    and model creation, the user is redirected to the client list view.

    Attributes:
        model (Client): The model associated with this view, representing
            the Client being created.
        form_class (ClientForm): The form class used to handle user input
            for the creation of a Client object.
        template_name (str): The path to the template file used to render
            this view.
        success_url (str): The URL to redirect to after successful client
            creation.
    """
    model = Client
    form_class = ClientForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:client_list')

class ClientUpdateView(ReferentialRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    """
    Handles the update functionality for Client objects.

    This class provides the mechanism to update an existing Client object using
    a form. It ensures that proper roles and permissions are enforced, maintains
    audit trails for changes, and resets the status of the object as needed. It
    uses a generic update view to manage the form rendering and submission process.

    Attributes:
        model (type): The model class that this view operates on. In this case,
            it is the Client model.
        form_class (type): The form class used to validate and process the data
            submitted for updating a Client object.
        template_name (str): The path to the template used for rendering the
            update form.
        success_url (type): The URL to redirect to upon successful update of the
            Client object.
    """
    model = Client
    form_class = ClientForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:client_list')

class ClientDeleteView(ReferentialRoleRequiredMixin, GenericDeleteView):
    """
    A view for handling deletion of Client objects.

    This view extends `GenericDeleteView` and enforces specific access control
    via the `ReferentialRoleRequiredMixin`. It is meant to handle the deletion
    of `Client` instances and redirect to a specified success URL upon completion.

    Attributes:
        model (Type[Model]): The model class being acted upon, which is `Client`
            in this case.
        success_url (str): The URL to redirect to after a successful deletion
            operation.
    """
    model = Client
    success_url = reverse_lazy('referential:client_list')


class ClientRestoreView(ReferentialRoleRequiredMixin, GenericRestoreView):
    """
    Handles the restoration of Client instances.

    This class is responsible for allowing the restoration of deleted Client
    instances via the user interface. It leverages the functionality of
    ReferentialRoleRequiredMixin to ensure the user has the necessary roles
    to perform the action and GenericRestoreView to handle the restore
    operation.

    Attributes:
        model: The model class that this view is responsible for restoring.
            For this view, it is set to `Client`.
        redirect_url (str): The URL to redirect to after a successful
            restore operation. In this view, it is set to
            'referential:client_list'.
    """
    model = Client
    redirect_url = 'referential:client_list'

class ClientDetailView(ReferentialRoleRequiredMixin, EntityDetailView):
    """View for displaying detailed information about a client.

    Provides functionality for displaying detailed information about a specific
    client within the application. Inherits from `ReferentialRoleRequiredMixin`
    and `EntityDetailView` to enforce access permissions and provide base
    functionality for handling entity detail views.

    Attributes:
        model (type): The model associated with this view, representing client
            data.
    """
    model = Client

class ClientValidateView(ReferentialRoleRequiredMixin, EntityValidateView):
    """
    Handles the validation process for Client entities.

    This class is responsible for managing the validation actions specific to
    Client instances within the application's referential framework. It extends
    the functionality provided by ReferentialRoleRequiredMixin and
    EntityValidateView to implement behavior tailored to client entities. The
    redirect URL directs users to the client list view upon successful operation.

    Attributes:
        model: The model class associated with this view, set to Client.
        redirect_url (str): The URL to redirect users to after successful validation.
    """
    model = Client
    redirect_url = 'referential:client_list'

class ClientRejectView(ReferentialRoleRequiredMixin, EntityRejectView):
    """
    Handles the rejection of client entities with specific access restrictions.

    This class is responsible for providing functionality to reject instances of the Client
    model. It enforces specific access control through the ReferentialRoleRequiredMixin
    and performs rejection operations through inheritance from EntityRejectView. Upon
    successful rejection of a Client instance, it redirects users to a predefined URL.

    Attributes:
        model (Type[Client]): The model class representing the Client entity being processed.
        redirect_url (str): The URL to which the user is redirected after rejecting a Client instance.
    """
    model = Client
    redirect_url = 'referential:client_list'

# ==========================================
# PROJECT VIEWS
# ==========================================
class ProjectListView(ReferentialRoleRequiredMixin, FilterStateMixin, ListView):
    """
    Displays a list of projects with specific filtering and search capabilities.

    This class provides a view to render a list of projects. It supports filtering,
    searching, and the inclusion of related data. It is built using Django's
    ListView along with custom mixins for additional functionality. The
    ReferentialRoleRequiredMixin ensures role-specific access to the view, while
    FilterStateMixin enables filter state persistence across requests.

    Attributes:
        model (type): The Django model associated with this view (Project).
        template_name (str): The template used to render the project list view.
        context_object_name (str): The name of the context variable that contains
            the list of projects.
        search_fields (list): The fields on which the search functionality is
            applied, including project name, project code, and client name.
    """
    model = Project
    template_name = 'referential/project_list.html'
    context_object_name = 'projects'
    search_fields = ['name', 'code', 'client__name']

    def get_queryset(self):
        return super().get_queryset().select_related('client', 'molecule_type')


class ProjectCreateView(ReferentialRoleRequiredMixin, AuditTrailMixin, CreateView):
    """
    Handles the creation of new Project entries in the system.

    This class is a specialized view that allows users to create new instances
    of the Project model. It provides form rendering, validation, and saving
    the data to the database. The view ensures that only authorized users
    with the required role can access it and also logs audit trails for any
    actions performed. The user is redirected to the project list page upon
    successful submission.

    Attributes:
        model (Model): The Project model that this view will create instances of.
        form_class (Form): The form class used for creating and validating
            Project instances.
        template_name (str): The path to the template used for rendering the
            form page.
        success_url (str): The URL to redirect the user to after successfully
            creating a Project instance.
    """
    model = Project
    form_class = ProjectForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:project_list')

class ProjectUpdateView(ReferentialRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    """
    Handles the update functionality for Project instances in the application.

    This class represents a view for updating existing Project objects. It leverages mixins to
    enforce role-based access control, maintain an audit trail of changes, and reset specific
    status fields when required. It provides a generic form-based interface for editing Project
    data, and redirects the user to a predefined list view upon successful update.

    Attributes:
        model: The model class associated with this view, representing the database table
            and logic for Project instances.
        form_class: The form class used to create and validate input data for Project updates.
        template_name: The path to the template file rendered for this view.
        success_url: The URL or URL pattern name where the view redirects after successfully
            processing the form.
    """
    model = Project
    form_class = ProjectForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:project_list')

class ProjectDeleteView(ReferentialRoleRequiredMixin, GenericDeleteView):
    """
    Handles the deletion of a Project instance.

    This class-based view provides functionality for deleting a specific
    Project object. It extends `GenericDeleteView` to inherit delete behavior
    and utilizes `ReferentialRoleRequiredMixin` to ensure proper access rights.

    Attributes:
        model (Type[Model]): The model associated with this delete view.
        success_url (str): The URL to redirect to upon successful deletion
            of a Project instance.
    """
    model = Project
    success_url = reverse_lazy('referential:project_list')

class ProjectRestoreView(ReferentialRoleRequiredMixin, GenericRestoreView):
    """
    Handles the restoration of Project instances.

    This class provides functionality for restoring instances of the Project model
    that were previously deleted or marked for restoration. It integrates with
    ReferentialRoleRequiredMixin to ensure proper permissions management and
    GenericRestoreView for base restoration behavior.

    Attributes:
        model (Model): The model class to be restored. In this case, it is Project.
        redirect_url (str): The URL to redirect to after a successful restoration.
    """
    model = Project
    redirect_url = 'referential:project_list'

class ProjectDetailView(ReferentialRoleRequiredMixin, EntityDetailView):
    """
    Represents a detailed view for a Project entity.

    This class is designed to handle the detailed view logic for the Project model
    within the application. The main purpose is to provide a complete representation
    of a specific Project instance while also enforcing role-based access control
    through inheritance of ReferentialRoleRequiredMixin.

    Attributes:
        model (Model): The model associated with this view, specifically the Project model.
    """
    model = Project

class ProjectValidateView(ReferentialRoleRequiredMixin, EntityValidateView):
    """
    Handles the validation of Project entities within the referential module.

    This class is responsible for managing the validation process for Project
    entities. It inherits from `ReferentialRoleRequiredMixin` and
    `EntityValidateView` to provide role-based access control and functionality
    for validating referential entities. Additionally, it specifies the model
    type and the URL to redirect upon completing validation.

    Attributes:
        model (Model): The model class associated with this validation view, which
            is `Project`.
        redirect_url (str): The URL to which the user will be redirected upon
            successful validation. In this case, it points to the project list
            view in the referential module.
    """
    model = Project
    redirect_url = 'referential:project_list'

class ProjectRejectView(ReferentialRoleRequiredMixin, EntityRejectView):
    """
    Handles the rejection of projects with specific role-based and entity-related requirements.

    This class provides functionality to reject a project entity while ensuring that the
    user fulfills the referential role requirements. It redirects to a predefined URL after
    successfully rejecting the project.

    Attributes:
        model (Type[Model]): The model class representing the project entity to be rejected.
        redirect_url (str): The URL to redirect to after the project rejection process is completed.
    """
    model = Project
    redirect_url = 'referential:project_list'

# ==========================================
# ANALYTICAL METHOD VIEWS
# ==========================================
class AnalyticalMethodListView(ReferentialRoleRequiredMixin, FilterStateMixin, ListView):
    """
    Handles the display of a list of analytical methods.

    This class serves to render a view for listing analytical methods
    within a referential system. It incorporates functionality to enforce
    specific role-based access control and supports filtering capabilities,
    providing a customizable and interactive user experience for managing
    analytical methods.

    Attributes:
        model: Specifies the model this view operates on, which is the
            AnalyticalMethod model.
        template_name (str): Specifies the path to the template file used
            to render the list view of analytical methods.
        context_object_name (str): Defines the name of the context variable
            representing the list of analytical methods passed to the template.
        search_fields (list of str): Specifies the fields of the AnalyticalMethod
            model that are searchable.
    """
    model = AnalyticalMethod
    template_name = 'referential/analytical_method_list.html'
    context_object_name = 'analytical_methods'
    search_fields = ['name']

class AnalyticalMethodCreateView(ReferentialRoleRequiredMixin, AuditTrailMixin, CreateView):
    """
    Handles the creation of new Analytical Method records.

    This class-based view is responsible for managing the form used to
    create a new Analytical Method record. It integrates role-based access
    controls and audit trail functionalities to ensure proper permissions
    and logging of creation events. The view utilizes a specified form
    class and template to render and process the required data.

    Attributes:
        model (AnalyticalMethod): The model associated with the view.
        form_class (type): The form class used for creating Analytical
            Method records.
        template_name (str): The name of the template for rendering the
            form.
        success_url (str): The URL to redirect to upon successful
            creation of an Analytical Method.
    """
    model = AnalyticalMethod
    form_class = AnalyticalMethodForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:analyticalmethod_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add New Analytical Method"
        return context

class AnalyticalMethodUpdateView(ReferentialRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    """
    Represents a view for updating an existing analytical method.

    This class provides the functionality required to update an existing analytical method
    object in the system. This includes rendering the appropriate form, handling user-inputted
    data, and ensuring the proper role-based access control and auditing requirements are met.
    Once updated, the user is redirected to the analytical method list page.

    Attributes:
        model (type): The model associated with this view, which is an AnalyticalMethod.
        form_class (type): The form class used for rendering and processing the update form.
        template_name (str): The path to the template used for rendering the update form view.
        success_url (type): The URL to redirect to upon successful form submission and
            update of the analytical method.
    """
    model = AnalyticalMethod
    form_class = AnalyticalMethodForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:analyticalmethod_list')

class AnalyticalMethodDeleteView(ReferentialRoleRequiredMixin, GenericDeleteView):
    """
    Handles the deletion of AnalyticalMethod objects.

    This class-based view enables the deletion of AnalyticalMethod instances from
    the database. It extends functionality provided by both ReferentialRoleRequiredMixin
    to enforce role-based authorization and GenericDeleteView for standard delete operations.

    Attributes:
        model (type): The model associated with the view, which is AnalyticalMethod.
        success_url (type): The URL to redirect to upon successful deletion of an
            AnalyticalMethod instance.
    """
    model = AnalyticalMethod
    success_url = reverse_lazy('referential:analyticalmethod_list')

class AnalyticalMethodRestoreView(ReferentialRoleRequiredMixin, GenericRestoreView):
    """
    Handles the restoration of AnalyticalMethod objects after deletion.

    This class provides functionality for restoring AnalyticalMethod objects that
    were previously deleted. It ensures that only users with the appropriate
    referential roles can perform this action. Upon successful restoration,
    it redirects users to a specified URL.

    Attributes:
        model: The model associated with this restore view, which is
            AnalyticalMethod.
        redirect_url (str): The name of the URL to redirect to following a
            successful restoration action.
    """
    model = AnalyticalMethod
    redirect_url = 'referential:analyticalmethod_list'

class AnalyticalMethodDetailView(ReferentialRoleRequiredMixin, EntityDetailView):
    """
    Handles the detailed view for an analytical method entity.

    This class provides a view to display details of the AnalyticalMethod
    model. It inherits from ReferentialRoleRequiredMixin and
    EntityDetailView to ensure proper role-based access control
    and common entity view patterns.

    Attributes:
        model (type): The model associated with this view, which is
            AnalyticalMethod.
    """
    model = AnalyticalMethod

class AnalyticalMethodValidateView(ReferentialRoleRequiredMixin, EntityValidateView):
    """
    Handles the validation of analytical methods in the referential module.

    This class is responsible for providing the necessary functionality to validate
    instances of the AnalyticalMethod model. It ensures that the user performing
    the action has the appropriate role through inheritance from
    ReferentialRoleRequiredMixin. After validation, it redirects the user to the
    appropriate analytical method list page.

    Attributes:
        model (type): The model class that this view operates on, which is
            AnalyticalMethod.
        redirect_url (str): The URL to redirect after the validation process is
            complete.
    """
    model = AnalyticalMethod
    redirect_url = 'referential:analyticalmethod_list'

class AnalyticalMethodRejectView(ReferentialRoleRequiredMixin, EntityRejectView):
    """
    Handles the rejection of an AnalyticalMethod entity through a specific view.

    This class is a specialized view that allows users with appropriate roles to
    reject an AnalyticalMethod entity and redirect them to the specified URL. It
    extends functionality from base mixins and views, ensuring adherence to
    referential integrity rules and user role requirements.

    Attributes:
        model (type): The model associated with this view, defining the type of
            entity being handled. In this case, it is the AnalyticalMethod class.
        redirect_url (str): URL to which the user is redirected after the rejection
            operation is successfully completed.
    """
    model = AnalyticalMethod
    redirect_url = 'referential:analyticalmethod_list'


def get_catalog_process():
    """
    Retrieves or creates a `Process` instance with the code `GLOBAL_CATALOG`. If the `Process` does
    not already exist, it is initialized with the default name "Global Unit Operation Catalog
    Repository" and status "DRAFT".

    Returns:
        Process: The retrieved or newly created `Process` instance.
    """
    process, created = Process.objects.get_or_create(
        code="GLOBAL_CATALOG",
        defaults={"name": "Global Unit Operation Catalog Repository", "status": "DRAFT"}
    )
    return process

# =========================================================================
# GLOBAL UNIT OPERATION VIEWS
# =========================================================================

class GlobalUnitOperationListView(ReferentialRoleRequiredMixin, FilterStateMixin, ListView):
    """
    Represents a view for displaying a list of global unit operations.

    Provides functionality to render a list of global unit operations from the
    database with specific template and context. It integrates role-based
    access control and mixins for managing filter states, ensuring that only
    authorized users and relevant filtered data are showcased.

    Attributes:
        model (GlobalUnitOperation): The model associated with the view.
        template_name (str): The path to the template used for rendering the view.
        context_object_name (str): The context variable name used to reference
            the list of global units in the template.
        search_fields (list): The fields used for enabling search functionality.
    """
    model = GlobalUnitOperation
    template_name = 'referential/global_unit_list.html'
    context_object_name = 'global_units'
    search_fields = ['name']


class GlobalUnitOperationCreateView(ReferentialRoleRequiredMixin, AuditTrailMixin, CreateView):
    """
    Defines a view for creating a new Global Unit Operation.

    This class extends the functionality of `CreateView` to provide an interface for
    creating instances of `GlobalUnitOperation`. It also incorporates referential role
    permissions and audit trail logging. The class specifies the model, form class,
    template, and redirection behavior after successful form submission.

    Attributes:
        model (GlobalUnitOperation): The model class used for the view.
        form_class (GlobalUnitOperationForm): The Django form class associated with
            the view.
        template_name (str): The path to the template used for rendering the view.
        success_url (str): The URL to redirect to upon successful form submission.
    """
    model = GlobalUnitOperation
    form_class = GlobalUnitOperationForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:globalunitoperation_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add New Global Unit Operation"
        return context


class GlobalUnitOperationUpdateView(ReferentialRoleRequiredMixin, AuditTrailMixin, StatusResetMixin, UpdateView):
    """
    Handles the updating of a Global Unit Operation.

    This view supports the updating of Global Unit Operation objects by associating
    a form, template, and required mixins to handle role-based access, audit logging,
    and status resetting. Once the update operation is complete, the user is redirected
    to the specified success URL.

    Attributes:
        model (GlobalUnitOperation): The model representing the Global Unit Operation.
        form_class (GlobalUnitOperationForm): The form class used to render and validate
            input data for the update.
        template_name (str): The path to the template used for rendering the form view.
        success_url (str): The URL to redirect to upon successful form submission.
    """
    model = GlobalUnitOperation
    form_class = GlobalUnitOperationForm
    template_name = 'generic/generic_form.html'
    success_url = reverse_lazy('referential:globalunitoperation_list')


class GlobalUnitOperationDeleteView(ReferentialRoleRequiredMixin, GenericDeleteView):
    """
    Handles the deletion of GlobalUnitOperation objects.

    This class is responsible for providing the functionality to delete
    GlobalUnitOperation objects in the system. It ensures that only users
    with the appropriate roles can perform this action and redirects to
    a predefined success URL upon deletion.

    Attributes:
        model (type): The model class associated with this view, which is
            GlobalUnitOperation.
        success_url (type): The URL to redirect to after successfully
            deleting a GlobalUnitOperation object.
    """
    model = GlobalUnitOperation
    success_url = reverse_lazy('referential:globalunitoperation_list')


class GlobalUnitOperationRestoreView(ReferentialRoleRequiredMixin, GenericRestoreView):
    """
    Represents a view for restoring deleted GlobalUnitOperation objects.

    This class is a specific implementation of a generic restore view, designed to
    handle the restoration of GlobalUnitOperation objects, which are assumed to be
    soft-deleted. Users can restore these objects to their active state through the
    functionality provided by this view. Permissions and role requirements for
    accessing this view are enforced by mixing in the `ReferentialRoleRequiredMixin`.

    Attributes:
        model: Specifies the model class used by this view. For this implementation,
            it is set to GlobalUnitOperation.
        redirect_url: Specifies the URL to which the user is redirected after the
            restore operation is successfully completed. Set to
            'referential:globalunitoperation_list'.
    """
    model = GlobalUnitOperation
    redirect_url = 'referential:globalunitoperation_list'


class GlobalUnitOperationDetailView(ReferentialRoleRequiredMixin, EntityDetailView):
    """
    Represents a detailed view for GlobalUnitOperation entities.

    This class integrates functionality for displaying detailed information
    about a GlobalUnitOperation entity, extending from the EntityDetailView
    and enforcing specific referential role requirements.

    Attributes:
        model (Type[GlobalUnitOperation]): Specifies the model class associated
            with this detail view.
    """
    model = GlobalUnitOperation


class GlobalUnitOperationValidateView(ReferentialRoleRequiredMixin, EntityValidateView):
    """
    Handles validation processes for global unit operations.

    This class is responsible for managing the validation logic for
    instances of the GlobalUnitOperation model. It extends
    ReferentialRoleRequiredMixin for role-based access control and
    EntityValidateView for core validation behavior. It also specifies
    a redirection URL to be used after validation operations.

    Attributes:
        model (type): The model associated with the validation process.
        redirect_url (str): The URL to redirect to after validation actions are
            completed.
    """
    model = GlobalUnitOperation
    redirect_url = 'referential:globalunitoperation_list'


class GlobalUnitOperationRejectView(ReferentialRoleRequiredMixin, EntityRejectView):
    """
    The GlobalUnitOperationRejectView class handles the rejection of GlobalUnitOperation
    instances with specific role-based permissions.

    This class ensures that only users with the required referential roles can perform the
    rejection operation. It inherits from ReferentialRoleRequiredMixin to enforce these
    permissions and from EntityRejectView to provide the rejection functionality. Upon
    successful rejection, the user is redirected to the specified URL.

    Attributes:
        model (type): Represents the model associated with this view, which is
            GlobalUnitOperation.
        redirect_url (type): Specifies the URL to redirect to after a successful rejection
            operation.
    """
    model = GlobalUnitOperation
    redirect_url = 'referential:globalunitoperation_list'