from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import re_path

from .models import Constraint, Participant, Project, TeamProject, TimeSlot
from .utils.timeslots_utils import (
    cancel_distribution,
    make_teams,
    get_teams,
    get_unallocated_students,
)
from .utils.notification_utils import notify_free_students, notify_teams


class TimeSlotInline(admin.TabularInline):
    model = TimeSlot


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "role",
        "tg_username",
        "level",
        "is_far_east",
    )
    list_filter = list_display

    readonly_fields = ("tg_id",)

    inlines = [
        TimeSlotInline,
    ]


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):

    list_display = (
        "participant",
        "participant_role",
        "time_slot",
        "team_project",
    )
    list_filter = (
        "participant",
        "time_slot",
        "team_project",
    )
    change_list_template = "admin/timeslot_change_list.html"

    def participant_role(self, timeslot):
        roles = dict(Participant.PARTICIPANT_ROLES_CHOICES)
        return roles[timeslot.participant.role]

    def get_urls(self):
        urls = super(TimeSlotAdmin, self).get_urls()
        custom_urls = [
            re_path(
                "^distribute/$",
                self.process_distribute_students,
                name="process_distribute_students",
            ),
            re_path(
                "^cancel_distribution/$",
                self.process_cancel_distribution_students,
                name="process_cancel_distribution_students",
            ),
            re_path(
                "^notify_teams/$",
                self.process_notify_teams,
                name="process_notify_teams",
            ),
            re_path(
                "^notify_free_students/$",
                self.process_notify_free_students,
                name="process_notify_free_students",
            ),
        ]
        return custom_urls + urls

    def process_distribute_students(self, request):
        result_message = make_teams()
        # TODO: использовать messages и level
        self.message_user(request, result_message)

        self.process_notify_teams(request)
        self.process_notify_free_students(request)

        return HttpResponseRedirect("../")

    def process_cancel_distribution_students(self, request):
        result_message = cancel_distribution()
        # TODO: использовать messages и level
        self.message_user(request, result_message)

        return HttpResponseRedirect("../")

    def process_notify_teams(self, request):
        # TODO: использовать messages и level
        notify_teams(get_teams())
        self.message_user(request, "Команды и ПМы оповещены.")

        return HttpResponseRedirect("../")

    def process_notify_free_students(self, request):
        # TODO: использовать messages и level
        notify_free_students(get_unallocated_students())
        self.message_user(request, "Нераспределенные ученики оповещены.")

        return HttpResponseRedirect("../")


@admin.register(TeamProject)
class TeamProjectAdmin(admin.ModelAdmin):
    pass


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    pass


@admin.register(Constraint)
class ConstraintAdmin(admin.ModelAdmin):
    pass
