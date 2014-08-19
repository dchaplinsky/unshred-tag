#!/usr/bin/env python

import click
from cli import admin as _admin
from prettytable import PrettyTable


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


@cli.group('batch')
def batch():
    """Manage batches"""
    pass


@batch.command("process")
@click.argument('wildcard_filter')
@click.argument('batch')
def batch_process(wildcard_filter, batch):
    """Process input files and upload processed batch to mongo"""
    from cli import load_to_mongo
    load_to_mongo.load_new_batch(wildcard_filter, batch)


@batch.command("list")
def batch_list():
    """Show all batches and stats"""
    from cli import load_to_mongo
    batches = load_to_mongo.list()
    x = PrettyTable(["Batch name", "Created", "Pages", "Shreds"])

    for b in batches:
        x.add_row([b["name"], b["created"], b["pages_processed"],
                   b["shreds_created"]])

    click.echo(x)

if __name__ == '__main__':
    cli()
