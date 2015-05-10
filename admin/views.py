# coding: utf-8
from flask.ext.admin.contrib.mongoengine import ModelView
from flask.ext import admin, login
from flask.ext.admin import expose
from flask.ext.admin.actions import ActionsMixin, action
from models import Cluster, Tags, User
from base import BaseModelView


class UserView(ModelView):
    column_filters = ['username']
    column_searchable_list = ('username',)
    column_exclude_list = ('password', 'name',)


class TagsView(ModelView, ActionsMixin):
    column_filters = ['title', 'is_base', 'category']
    column_exclude_list = ('description',)
    column_default_sort = ('created_at', True)

    def __init__(self, *args, **kwargs):
        super(TagsView, self).__init__(*args, **kwargs)
        self.init_actions()

    @action('toggle_base_state', 'Toggle Is Base')
    def toggle_base_state(self, ids):
        for tag in Tags.objects.filter(pk__in=ids).only('pk', 'is_base'):
            tag.is_base = not tag.is_base
            tag.save()


class ClusterView(ModelView):
    column_list = ['id', 'users_count', 'users_skipped', 'users_processed',
                   'batch', 'all_tags', 'render_auto_tags', 'num_members',
                   'image_html']


class BaseAdminIndexView(admin.AdminIndexView):
    def is_accessible(self):
        try:
            return login.current_user.is_admin()
        except AttributeError:
            pass
        return False


class CustomShredsView(BaseModelView):

    def __unicode__(self):
        return "Shred: %s" % self.id

    @expose('/')
    def index_view(self):
        # Grab parameters from URL
        page, sort_idx, sort_desc, search = self._get_list_extra_args()

        page_size = 10
        count = Cluster._get_collection().count()
        num_pages = count // page_size
        if count % page_size != 0:
            num_pages += 1

        data = Cluster._get_collection().find(
            {},
            {}).skip(page * page_size).limit(page_size)

        # Various URL generation helpers
        def pager_url(p):
            # Do not add page number if it is first page
            if p == 0:
                p = None

            return self._get_url('.index_view', p, sort_idx, sort_desc,
                                 search)

        return self.render('admin/shreds.html', data=data, count=count,
                           pager_url=pager_url,
                           num_pages=num_pages,
                           page=page,)


def admin_init(app):
    from flask.ext import admin
    admin = admin.Admin(app, 'Unshred', index_view=BaseAdminIndexView())
    admin.add_view(UserView(User))
    admin.add_view(TagsView(Tags))
    admin.add_view(ClusterView(Cluster))
    admin.add_view(CustomShredsView(name='Custom Shreds'))
