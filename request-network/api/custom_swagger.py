from fastapi.responses import HTMLResponse

def get_swagger_ui_html(
    *,
    openapi_url: str,
    title: str,
) -> HTMLResponse:
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link type="text/css" rel="stylesheet" href="/static/swagger-ui.css">
        <title>{title}</title>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="/static/swagger-ui-bundle.js"></script>
        <script>
        const ui = SwaggerUIBundle({{
            url: '{openapi_url}',
            dom_id: '#swagger-ui',
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.SwaggerUIStandalonePreset
            ],
            persistAuthorization: true,
        }})
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
