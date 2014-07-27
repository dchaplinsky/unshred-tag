import click
from cli import admin as _admin

@click.group()
def cli():
    """Unshred.it management CLI"""

@cli.group('admin')
def admin():
    """Manages admin users"""
    pass

@admin.command('list')
def admin_list():
    """List admin users"""
    _admin.list_admin()

@admin.command('add')
@click.argument('email')
def admin_add(email):
    """Mark user as admin"""
    _admin.toggle_admin(email, True)

@admin.command('remove')
@click.argument('email')
def admin_remove(email):
    """Unmark user as admin"""
    _admin.toggle_admin(email, False)

if __name__ == '__main__':
    cli()

