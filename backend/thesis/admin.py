from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib import messages
from reversion.admin import VersionAdmin
from unfold.admin import ModelAdmin

from thesis.models import (Chapter, ChapterRevision, ConsistencyRow, EvidenceLink, Indicator,
                           Instrument, InstrumentItem, McpAccessToken, Project,
                           ProjectParticipant, ResearchProfile, ResearchVariable, ReviewComment,
                           ReviewEvent, SourceMetadataCheck, StepProgress, User,
                           VariableDimension)
from thesis.services.errors import DomainError
from thesis.services.reviews import decide_chapter


class AdvisorScopedAdmin:
    project_lookup = "project"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if request.user.is_superuser:
            return queryset
        return queryset.filter(**{
            f"{self.project_lookup}__participants__user": request.user,
            f"{self.project_lookup}__participants__role": ProjectParticipant.Role.ADVISOR,
            f"{self.project_lookup}__participants__active": True,
        }).distinct()


class ReadOnlyForAdvisors:
    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if request.user.is_superuser:
            return fields
        return tuple(field.name for field in self.model._meta.fields)

    def has_add_permission(self, request):
        return request.user.is_superuser and super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser and super().has_delete_permission(request, obj)


@admin.register(User)
class ThesisUserAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "display_name", "is_staff", "is_active")
    search_fields = ("email", "display_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Perfil", {"fields": ("display_name", "first_name", "last_name")}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "display_name", "password1", "password2")}),)


@admin.register(Project)
class ProjectAdmin(AdvisorScopedAdmin, ReadOnlyForAdvisors, VersionAdmin, ModelAdmin):
    list_display = ("name", "title", "status", "updated_at")
    search_fields = ("name", "title")


@admin.register(ProjectParticipant)
class ProjectParticipantAdmin(AdvisorScopedAdmin, ReadOnlyForAdvisors, ModelAdmin):
    list_display = ("project", "user", "role", "active")
    list_filter = ("role", "active")


@admin.register(ResearchProfile)
class ResearchProfileAdmin(AdvisorScopedAdmin, ReadOnlyForAdvisors, VersionAdmin, ModelAdmin):
    list_display = ("project", "approach", "ods_code", "lock_version", "updated_at")


@admin.register(ConsistencyRow)
class ConsistencyRowAdmin(AdvisorScopedAdmin, ReadOnlyForAdvisors, ModelAdmin):
    list_display = ("project", "ordinal", "objective_text", "question_text")
    list_filter = ("ordinal",)
    search_fields = ("project__name", "objective_text", "question_text", "hypothesis_text")


@admin.register(ResearchVariable)
class ResearchVariableAdmin(AdvisorScopedAdmin, ReadOnlyForAdvisors, ModelAdmin):
    list_display = ("project", "ordinal", "role", "name")
    list_filter = ("role",)
    search_fields = ("project__name", "name")


@admin.register(VariableDimension)
class VariableDimensionAdmin(AdvisorScopedAdmin, ReadOnlyForAdvisors, ModelAdmin):
    project_lookup = "variable__project"
    list_display = ("variable", "ordinal", "name")
    search_fields = ("variable__name", "name")


@admin.register(Indicator)
class IndicatorAdmin(AdvisorScopedAdmin, ReadOnlyForAdvisors, ModelAdmin):
    project_lookup = "dimension__variable__project"
    list_display = ("dimension", "ordinal", "name", "measurement_scale")
    list_filter = ("measurement_scale",)
    search_fields = ("dimension__name", "name")


@admin.register(Instrument)
class InstrumentAdmin(AdvisorScopedAdmin, ReadOnlyForAdvisors, ModelAdmin):
    list_display = ("project", "name", "kind", "version_no", "status", "created_at")
    list_filter = ("kind", "status")
    search_fields = ("project__name", "name")


@admin.register(InstrumentItem)
class InstrumentItemAdmin(AdvisorScopedAdmin, ReadOnlyForAdvisors, ModelAdmin):
    project_lookup = "instrument__project"
    list_display = ("instrument", "ordinal", "dimension", "response_scale")
    search_fields = ("instrument__name", "prompt_text")


@admin.register(StepProgress)
class StepProgressAdmin(AdvisorScopedAdmin, ModelAdmin):
    list_display = ("project", "step_code", "status", "completed_at")
    list_filter = ("step_code", "status")
    readonly_fields = ("project", "step_code", "status", "output_json", "completed_at", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Chapter)
class ChapterAdmin(AdvisorScopedAdmin, ModelAdmin):
    list_display = ("project", "number", "status", "approved_at", "updated_at")
    list_filter = ("number", "status")
    search_fields = ("project__name", "project__title")
    readonly_fields = ("project", "number", "status", "approved_revision", "approved_at", "created_at", "updated_at")
    actions = ("approve_selected", "request_changes_selected")

    @admin.action(description="Aprobar capítulos seleccionados sin observaciones abiertas")
    def approve_selected(self, request, queryset):
        for chapter in queryset:
            try:
                decide_chapter(request.user, chapter.project_id, chapter.number, ReviewEvent.Action.APPROVE)
            except DomainError as exc:
                self.message_user(request, f"{chapter}: {exc.message}", level=messages.ERROR)

    @admin.action(description="Solicitar cambios en capítulos con observaciones abiertas")
    def request_changes_selected(self, request, queryset):
        for chapter in queryset:
            try:
                decide_chapter(request.user, chapter.project_id, chapter.number, ReviewEvent.Action.REQUEST_CHANGES)
            except DomainError as exc:
                self.message_user(request, f"{chapter}: {exc.message}", level=messages.ERROR)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ChapterRevision)
class ChapterRevisionAdmin(AdvisorScopedAdmin, ModelAdmin):
    project_lookup = "chapter__project"
    list_display = ("chapter", "revision_no", "step_code", "created_by", "created_at")
    readonly_fields = ("chapter", "revision_no", "step_code", "idempotency_key", "content_md",
                       "content_sha256", "created_by", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ReviewComment)
class ReviewCommentAdmin(AdvisorScopedAdmin, ModelAdmin):
    project_lookup = "revision__chapter__project"
    list_display = ("revision", "author", "status", "created_at")
    list_filter = ("status",)
    readonly_fields = ("revision", "author", "start_cp", "end_cp", "selected_text", "body",
                       "status", "resolved_by", "resolved_at", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ReviewEvent)
class ReviewEventAdmin(AdvisorScopedAdmin, ModelAdmin):
    project_lookup = "chapter__project"
    list_display = ("chapter", "action", "actor", "created_at")
    readonly_fields = ("chapter", "revision", "actor", "action", "reason", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SourceMetadataCheck)
class SourceMetadataCheckAdmin(AdvisorScopedAdmin, ModelAdmin):
    project_lookup = "source__project"
    list_display = ("source", "doi", "registry", "checked_at")
    readonly_fields = ("source", "doi", "registry", "registered_title", "registered_authors_json",
                       "title_similarity", "registry_record_json", "checked_at")

    def has_add_permission(self, request):
        return False


@admin.register(EvidenceLink)
class EvidenceLinkAdmin(AdvisorScopedAdmin, ModelAdmin):
    list_display = ("project", "excerpt", "status", "created_by", "reviewed_by", "created_at")
    list_filter = ("status",)
    readonly_fields = ("project", "revision", "excerpt", "claim_text", "start_char", "end_char",
                       "matched_text", "excerpt_sha256", "status", "created_by", "reviewed_by",
                       "review_note", "reviewed_at", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(McpAccessToken)
class McpAccessTokenAdmin(ModelAdmin):
    list_display = ("user", "expires_at", "revoked_at")
    readonly_fields = ("token_hash", "created_at")

    def has_add_permission(self, request):
        return False
