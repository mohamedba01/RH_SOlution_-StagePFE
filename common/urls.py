import os

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve

from candidats import views as candidats_views
from stages import views

urlpatterns = [
    path('', RedirectView.as_view(url='/admin/', permanent=True), name='home'),

    path('admin/', admin.site.urls),

    path('import_students/', views.StudentImportView.as_view(), name='import-students'),
    path('import_students_ester/', views.imports.StudentEsterImportView.as_view(), name='import-students-ester'),
    path('import_hp/', views.HPImportView.as_view(), name='import-hp'),
    path('import_hp_contacts/', views.HPContactsImportView.as_view(), name='import-hp-contacts'),

    path('attribution/', views.AttributionView.as_view(), name='attribution'),
    re_path(r'^stages/export/(?P<scope>all)?/?$', views.export.stages_export, name='stages_export'),

    path('institutions/', views.CorporationListView.as_view(), name='corporations'),
    path('institutions/<int:pk>/', views.CorporationView.as_view(), name='corporation'),
    path('institutions/merge/', views.CorporationMergeView.as_view(), name='corporations-merge'),
    path('institutions/export/', views.export.institutions_export, name='corporations-export'),

    path('classes/', views.KlassListView.as_view(), name='classes'),
    path('classes/<int:pk>/', views.KlassView.as_view(), name='class'),
    path('classes/<int:pk>/import_reports/', views.ImportReportsView.as_view(),
        name='import-reports'),
    path('classes/print_klass_list/', views.PrintKlassList.as_view(), name='print-klass-list'),
    path('student/<int:pk>/comment/', views.StudentCommentView.as_view(), name='student-comment'),

    path('candidate/<int:pk>/send_convocation/', candidats_views.ConvocationView.as_view(),
        name='candidate-convocation'),
    path('candidate/<int:pk>/send_confirmation/', candidats_views.ConfirmationView.as_view(),
        name='candidate-confirmation'),
    path('candidate/<int:pk>/send_validation/', candidats_views.ValidationView.as_view(),
        name='candidate-validation'),
    path('candidate/<int:pk>/summary/', candidats_views.inscription_summary, name='candidate-summary'),

    path('student/<int:pk>/examination/mentor/', views.PrintCompensationForm.as_view(), {'typ': 'mentor'},
        name='print-mentor-compens-form'),
    path('exam/<int:pk>/indemn/<slug:typ>/', views.PrintCompensationForm.as_view(),
        name='print-compens-form'),

    # Qualification EDE
    path('student_ede/<int:pk>/send_convocation/', views.StudentConvocationExaminationView.as_view(),
        name='student-ede-convocation'),
    path('student_ede/<int:pk>/examination/expert/', views.PrintExpertEDECompensationForm.as_view(),
        name='print-expert-letter-ede'),

    # Qualification EDS
    path('student_eds/<int:pk>/send_convocation/', views.StudentConvocationEDSView.as_view(),
        name='student-eds-convocation'),
    path('student_eds/<int:pk>/examination/expert/', views.PrintExpertEDSCompensationForm.as_view(),
        name='print-expert-letter-eds'),

    path('student/export_qualif/<slug:section>/', views.export.export_qualification,
        name='export-qualif'),

    path('imputations/export/', views.export.imputations_export, name='imputations_export'),
    path('export_sap/', views.export.export_sap, name='export_sap'),
    path('print/update_form/', views.PrintUpdateForm.as_view(), name='print_update_form'),
    path('print/charge_sheet/', views.PrintChargeSheet.as_view(), name='print-charge-sheet'),
    path('general_export/', views.export.general_export, name='general-export'),
    path('ortra_export/', views.export.ortra_export, name='ortra-export'),

    # AJAX/JSON urls
    path('section/<int:pk>/periods/', views.section_periods, name='section_periods'),
    path('section/<int:pk>/classes/', views.section_classes, name='section_classes'),
    path('period/<int:pk>/students/', views.period_students, name='period_students'),
    path('period/<int:pk>/corporations/', views.period_availabilities, name='period_availabilities'),
    # Training params in POST:
    path('training/new/', views.new_training, name="new_training"),
    path('training/del/', views.del_training, name="del_training"),
    path('training/by_period/<int:pk>/', views.TrainingsByPeriodView.as_view()),

    path('student/<int:pk>/summary/', views.StudentSummaryView.as_view()),
    path('student/<int:pk>/send_reports/sem/<int:semestre>/', views.SendStudentReportsView.as_view(),
        name='send-student-reports'),
    path('availability/<int:pk>/summary/', views.AvailabilitySummaryView.as_view()),
    path('corporation/<int:pk>/contacts/', views.CorpContactJSONView.as_view()),

    path('summernote/', include('django_summernote.urls')),
    # Serve bulletins by Django to allow LoginRequiredMiddleware to apply
    path('media/bulletins/<path:path>', serve,
        {'document_root': os.path.join(settings.MEDIA_ROOT, 'bulletins'), 'show_indexes': False}
    ),
]
