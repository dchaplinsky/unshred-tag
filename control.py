#!/usr/bin/env python

import click
from cli import admin as _admin
from prettytable import PrettyTable
import metrics


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


@cli.group('tags')
def tags():
    """Manage tags"""
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
    batches = load_to_mongo.list_batches()
    x = PrettyTable(["Batch name", "Shreds"])

    for b in batches:
        x.add_row([b["name"], b["shreds_created"]])

    click.echo(x)


@tags.command("import")
@click.option('--clear/--no-clear', default=False,
              help='delete existing base tags before import')
def tags_import(clear):
    """Import base tags from fixtures"""
    from cli import load_to_mongo
    added, updated = load_to_mongo.import_tags(clear)
    click.echo(u"%s tags created, %s tags updated" % (added, updated))


@tags.command("list")
def tags_list():
    """List tags in db"""
    from cli import load_to_mongo

    tags = load_to_mongo.list_tags()
    x = PrettyTable(["Tag name", "Is base", "Used"])

    for tag in tags:
        x.add_row([tag["title"], tag["is_base"], tag["usages"]])

    click.echo(x)


@cli.group('metric')
def metric():
    """Manage Shreds metrics"""
    pass


@metric.command('jaccard')
@click.option('--clear/--no-clear', default=False,
              help='delete existing shreds distances before inserting new')
@click.option('--repeats', default=metrics.TAGS_REPEATS)
def churn_jaccard(clear, repeats):
    metrics.churn_jaccard(clear, repeats)

if __name__ == '__main__':
    cli()
