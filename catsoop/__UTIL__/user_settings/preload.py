import html

cs_auth_required = True
cs_view_without_auth = False
cs_long_name = cs_content_header = "CAT-SOOP: User Settings"
_course = cs_form.get("course", None)
_ctx = csm_loader.generate_context([_course] if _course is not None else [])
