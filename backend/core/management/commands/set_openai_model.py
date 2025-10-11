"""Management command to set the OpenAI model for image processing."""

from django.core.management.base import BaseCommand, CommandError

from core.models import Settings
from core.services.types import ModelType


MODEL_HELP = "\n".join(f"    {m.value:<22} : {m.title}" for m in ModelType)


class Command(BaseCommand):
    help = (
        "Set the OpenAI model for image processing.\n\n"
        "Available models:\n"
        f"{MODEL_HELP}\n\n"
        "A model is required."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "model",
            type=str,
            help="The OpenAI model to use (required)",
            choices=[m.value for m in ModelType],
        )

    def handle(self, *args, **options):
        # Show current model if no arguments provided
        settings = Settings.get_settings()
        model = options["model"]

        # Validate model
        try:
            model_type = ModelType(model)
        except ValueError:
            valid_models = "\n".join(f"  {m.value:<22} : {m.title}" for m in ModelType)
            raise CommandError(f"Invalid model: {model}\n\nAvailable models:\n{valid_models}")

        # Update setting
        settings.openai_model = model
        settings.save()

        self.stdout.write(self.style.SUCCESS(f"OpenAI model set to: {model_type.title}\n"))
