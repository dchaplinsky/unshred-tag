from flask import request, url_for
from flask.ext.admin import BaseView, expose
from flask.ext.admin._backwards import ObsoleteAttr
from jinja2 import contextfunction


class BaseModelView(BaseView):
    column_sortable_list = ObsoleteAttr('column_sortable_list',
                                        'sortable_columns',
                                        None)
    column_descriptions = None

    def _get_url(self, view=None, page=None, sort=None, sort_desc=None,
                 search=None):
        if not search:
            search = None

        if not page:
            page = None

        kwargs = dict(page=page, sort=sort, desc=sort_desc, search=search)

        return url_for(view, **kwargs)

    def _get_list_extra_args(self):
        """
            Return arguments from query string.
        """
        page = request.args.get('page', 0, type=int)
        sort = request.args.get('sort', None, type=int)
        sort_desc = request.args.get('desc', None, type=int)
        search = request.args.get('search', None)

        return page, sort, sort_desc, search

    @expose('/action/', methods=('POST',))
    def action_view(self):
        return self.handle_action()

    def is_sortable(self, name):
        return name in self.get_sortable_columns()

    def get_sortable_columns(self):
        if self.column_sortable_list is None:
            return dict()
        else:
            result = dict()

            for c in self.column_sortable_list:
                if isinstance(c, tuple):
                    result[c[0]] = c[1]
                else:
                    result[c] = c

            return result

    @contextfunction
    def get_list_value(self, context, model, name):
        return model[name]
