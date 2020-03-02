# EOL DIRECT MESSAGE

Direct message between two students inside a course.

## Configurations

To enable email tasks edit *production.py* in *lms settings* and add:
> CELERY_IMPORTS = ("eol_directmessage.tasks",)

## Send Reminder Mail (Manual)

    > docker-compose exec lms python manage.py lms --settings=tutor.production reminder_mail


## TODO

- [ ] Crontab
- [ ] Reload Button
- [ ] Tests