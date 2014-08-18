# coding: utf-8
from flask.ext.admin.contrib.mongoengine import ModelView
from flask.ext import admin, login
from flask.ext.admin import expose
from models import Shreds, Tags, User
from base import BaseModelView


class UserView(ModelView):
    column_filters = ['username']
    column_searchable_list = ('username',)
    column_exclude_list = ('password', 'name',)


class TagsView(ModelView):
    column_filters = ['title']
    column_exclude_list = ('description',)


class ShredsView(ModelView):
    pass


class BaseAdminIndexView(admin.AdminIndexView):
    def is_accessible(self):
        try:
            return login.current_user.is_admin()
        except AttributeError:
            return False
        else:
            return False


class CustomShredsView(BaseModelView):

    @expose('/')
    def index_view(self):
        # Grab parameters from URL
        page, sort_idx, sort_desc, search = self._get_list_extra_args()

        page_size = 10
        count = Shreds._get_collection().count()
        num_pages = count // page_size
        if count % page_size != 0:
            num_pages += 1

        data = Shreds._get_collection().find(
            {},
            {'contour': 0}).skip(page * page_size).limit(page_size)

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


class UsersView(BaseModelView):
    column_sortable_list = ('username', 'used_tags', 'tags_count',
                            'shreds_count', 'skipped_count', 'last_login')
    column_labels = [
        ('username', 'username'),
        ('used_tags', 'used_tags'),
        ('tags_count', 'tags_count'),
        ('shreds_count', 'shreds_count'),
        ('skipped_count', 'skipped_count'),
        ('last_login', 'last_login')]

    column_descriptions = dict(
        username='', used_tags='', tags_count='', shreds_count='',
        skipped_count='', last_login='')

    @expose('/')
    def index_view(self):
        # Grab parameters from URL
        page, sort_idx, sort_desc, search = self._get_list_extra_args()

        page_size = 10
        count = User._get_collection().count()
        num_pages = count // page_size
        if count % page_size != 0:
            num_pages += 1

        data = User._get_collection().find({}, {'password': 0})
        result = []
        for d in data:
            temp_dict = {}
            temp_dict['username'] = d['username']
            temp_dict['last_login'] = d.get('last_login', None)
            temp_dict['used_tags'] = []
            temp_dict['tags_count'] = 0
            temp_dict['shreds_count'] = 0
            temp_dict['skipped_count'] = 0

            shreds = Shreds._get_collection().find(
                {"tags.user": str(d["_id"])})

            for s in shreds:
                for tag in s['tags']:
                    if tag['user'] == str(d["_id"]):
                        if tag['tags'] == 'skipped':
                            temp_dict['skipped_count'] += 1
                        else:
                            temp_dict['shreds_count'] += 1
                            temp_dict['used_tags'] += tag['tags']
                            temp_dict['tags_count'] += len(tag['tags'])

            temp_dict['used_tags'] = list(set(temp_dict['used_tags']))
            result.append(temp_dict)

        # Various URL generation helpers
        def pager_url(p):
            # Do not add page number if it is first page
            if p == 0:
                p = None

            return self._get_url('.index_view', p, sort_idx, sort_desc,
                                 search)

        def sort_url(column, invert=False):
            desc = None

            if invert and not sort_desc:
                desc = 1

            return self._get_url('.index_view', page, column, desc,
                                 search)

        return self.render('admin/users.html', data=result, count=count,
                           pager_url=pager_url,
                           num_pages=num_pages,
                           page=page,
                           list_columns=self.column_labels,
                           sort_url=sort_url,
                           get_value=self.get_list_value)


def admin_init(app):
    from flask.ext import admin
    admin = admin.Admin(app, 'Unshred', index_view=BaseAdminIndexView())
    admin.add_view(UserView(User))
    admin.add_view(TagsView(Tags))
    admin.add_view(ShredsView(Shreds))
    admin.add_view(CustomShredsView(name='Custom Shreds'))
    admin.add_view(UsersView(name='Custom Users'))
