from django.urls import path
from .views import AssignRecordView, CreateRecordView, RecordListView, UpdateRecordView, DeleteRecordView, RecordDetailView

urlpatterns = [
    path('', RecordListView.as_view(), name='record-list'),
    path('create/', CreateRecordView.as_view(), name='record-create'),
    path('assign/', AssignRecordView.as_view(), name='assign-record'),
    path('<str:record_id>/', RecordDetailView.as_view(), name='record-detail'),
    path('<str:record_id>/update/', UpdateRecordView.as_view(), name='record-update'),
    path('<str:record_id>/delete/', DeleteRecordView.as_view(), name='record-delete'),
]