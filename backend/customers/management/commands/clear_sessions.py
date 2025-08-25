"""
Management command to clear user sessions.
"""

from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Clear all sessions or sessions for a specific user"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-email",
            type=str,
            help="Clear sessions for a specific user email",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Clear all sessions",
        )
        parser.add_argument(
            "--expired",
            action="store_true",
            help="Clear only expired sessions",
        )

    def handle(self, *args, **options):
        if options["expired"]:
            # Clear expired sessions
            Session.objects.filter(expire_date__lt=timezone.now()).delete()
            self.stdout.write(self.style.SUCCESS("Cleared all expired sessions"))

        elif options["all"]:
            # Clear all sessions
            count = Session.objects.all().count()
            Session.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"Cleared {count} sessions"))

        elif options["user_email"]:
            # Clear sessions for specific user
            from django.contrib.auth import get_user_model

            User = get_user_model()

            try:
                user = User.objects.get(email=options["user_email"])
                count = 0
                for session in Session.objects.all():
                    session_data = session.get_decoded()
                    if str(session_data.get("_auth_user_id")) == str(user.id):
                        session.delete()
                        count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Cleared {count} sessions for user {options['user_email']}")
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User with email {options['user_email']} not found")
                )
        else:
            self.stdout.write(
                self.style.WARNING("Please specify --all, --expired, or --user-email")
            )
