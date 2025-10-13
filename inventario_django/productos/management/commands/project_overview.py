from django.core.management.base import BaseCommand
from django.conf import settings
from django.urls import get_resolver
from django.apps import apps
import os, sys, textwrap

class Command(BaseCommand):
    help = "Genera un resumen del proyecto (ligero) en project_overview.md"

    def handle(self, *args, **kwargs):
        out = "project_overview.md"
        lines = []
        add = lines.append

        add(f"# Resumen de Proyecto\n")
        add(f"- Django: {self.get_django_version()}")
        add(f"- Base dir: {settings.BASE_DIR}\n")

        add("## INSTALLED_APPS (no Django por defecto)\n")
        core = ("django.", "mkdocs", "whitenoise")
        for app in settings.INSTALLED_APPS:
            if not app.startswith(core):
                add(f"- {app}")
        add("")

        add("## Base de datos (tipo)\n")
        db = settings.DATABASES.get("default", {})
        add(f"- ENGINE: {db.get('ENGINE','')}")
        add(f"- NAME:   {db.get('NAME','')}\n")

        add("## Modelos y campos\n")
        for m in apps.get_models():
            add(f"### {m.__module__}.{m.__name__}")
            for f in m._meta.fields:
                rel = ""
                rf = getattr(f, "remote_field", None)
                if rf and rf.model:
                    rel = f" → {rf.model.__module__}.{rf.model.__name__}"
                add(f"- **{f.name}**: {f.get_internal_type()}{rel}")
            add("")
        
        add("## URLs\n")
        try:
            for line in self.dump_urls():
                add(line)
        except Exception as e:
            add(f"_No se pudieron enumerar URLs: {e}_")
        add("")

        add("## Templates (carpeta templates/)\n")
        tpl_dir = os.path.join(settings.BASE_DIR, "templates")
        if os.path.isdir(tpl_dir):
            for root, _, files in os.walk(tpl_dir):
                for f in files:
                    add("- " + os.path.relpath(os.path.join(root, f), settings.BASE_DIR))
        else:
            add("_No se encontró carpeta templates/_")
        add("")

        with open(out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))

        self.stdout.write(self.style.SUCCESS(f"Generado: {out}"))

    def dump_urls(self):
        resolver = get_resolver()
        yield from self._flatten("", resolver.url_patterns)

    def _flatten(self, prefix, patterns):
        for p in patterns:
            if hasattr(p, "url_patterns"):
                yield from self._flatten(prefix + str(p.pattern), p.url_patterns)
            else:
                name = p.name or ""
                target = getattr(p, "lookup_str", "view")
                yield f"- `{prefix}{p.pattern}`  [{name}] → {target}"

    def get_django_version(self):
        try:
            import django
            return django.get_version()
        except Exception:
            return "desconocida"
