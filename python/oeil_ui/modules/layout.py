from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="python/oeil_ui/templates")


def render(request, template_name, context=None, **kwargs):

    if context is None:
        context = {}

    context.update(kwargs)

    return templates.TemplateResponse(
        template_name,
        {
            "request": request,
            **context
        }
    )