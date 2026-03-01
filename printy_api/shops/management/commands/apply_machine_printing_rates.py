"""
Apply default printing rates to a machine (optional).
Uses templates by sheet size (A4, A3, SRA3).
"""
from django.core.management.base import BaseCommand

from printy_api.shops.models import Machine
from printy_api.shops.printing_rates import apply_default_printing_rates


class Command(BaseCommand):
    help = "Apply default printing rates (cost_per_impression, gsm range) to a machine"

    def add_arguments(self, parser):
        parser.add_argument(
            "--machine",
            type=int,
            required=True,
            help="Machine ID",
        )

    def handle(self, *args, **options):
        machine_id = options["machine"]
        machine = Machine.objects.filter(pk=machine_id).first()

        if not machine:
            self.stderr.write(
                self.style.ERROR(f"Machine not found: {machine_id}")
            )
            return

        if apply_default_printing_rates(machine):
            self.stdout.write(
                self.style.SUCCESS(
                    f"Applied default printing rates to {machine.name} "
                    f"(sheet_size={machine.sheet_size.name})"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"No template for sheet size '{machine.sheet_size.name if machine.sheet_size else 'None'}'. "
                    "Machine unchanged."
                )
            )
