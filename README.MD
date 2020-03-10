# EOL DIRECT MESSAGE

![https://github.com/eol-uchile/eol_directmessage/actions](https://github.com/eol-uchile/eol_directmessage/workflows/Python%20application/badge.svg)

Direct message between two students inside a course.

## Configurations

To enable email tasks edit *production.py* in *lms settings* and add:
> CELERY_IMPORTS = ("eol_directmessage.tasks",)

## Send Reminder Mail (Manual)

    > docker-compose exec lms python manage.py lms --settings=tutor.production reminder_mail

## TESTS
**Prepare tests:**

    > cd .github/
    > docker-compose run lms /openedx/requirements/eol_directmessage/.github/test.sh


## TODO

- [ ] Crontab
- [x] Reload Button
- [ ] Tests