from app import db #required for init db
from models import User
from click import echo

def list_admin():
    users = list(User.objects(admin=True).scalar("email"))
    if len(users) == 0:
        echo("No admins found")
        return

    echo("Allowed admins are")
    for email in users:
        echo("- %s" % email)

def toggle_admin(email, state):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        echo("User %s does not exists" % email)

    user.admin = state
    user.save()
    echo("Done")
