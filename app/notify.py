import json
from app import app, db
from app.models import Notify, Tasks, Users, Subscription
from app.email import send_email
from datetime import datetime
from pywebpush import webpush, WebPushException

class NotifySend(object):

    def __init__(self, id_task, current_user):
        self.task = Tasks.query.filter_by(id=id_task).first()
        if current_user:
            self.id_current_user = current_user.id
            self.id_partner_user = current_user.get_id_partner_by_id_user(current_user.id)
        else:
            current_user = Users.query.filter_by(id=self.task.create_user).first()
            self.id_current_user = current_user.id
            self.email_current_user = current_user.email
            self.is_send_email_current_user = current_user.is_send_email

            self.id_partner_user = current_user.get_id_partner_by_id_user(current_user.id)
            partner_user = Users.query.filter_by(id=self.id_partner_user).first()
            self.email_partner_user = partner_user.email
            self.is_send_email_partner_user = partner_user.is_send_email

    def add_notify(self):
        self.task.create_date = datetime.strptime(self.task.create_date.strftime('%Y-%m-%d %H:%M:%S'),
                                                  '%Y-%m-%d %H:%M:%S')
        self.task.deadline = datetime.strptime(self.task.deadline.strftime('%Y-%m-%d %H:%M:%S'),
                                               '%Y-%m-%d %H:%M:%S')
        date_deadline_25_percent = self.task.create_date + ((self.task.deadline - self.task.create_date) * 0.25)
        date_deadline_50_percent = self.task.create_date + ((self.task.deadline - self.task.create_date) * 0.5)
        date_deadline_75_percent = self.task.create_date + ((self.task.deadline - self.task.create_date) * 0.75)

        if datetime.now() < date_deadline_25_percent:
            notify_deadline_25_webpush_cu = Notify(type='deadline_25', method='webpush', time=date_deadline_25_percent,
                                               id_recipient=self.id_current_user, id_task=self.task.id)
            notify_deadline_25_email_cu = Notify(type='deadline_25', method='email', time=date_deadline_25_percent,
                                              id_recipient=self.id_current_user, id_task=self.task.id)
            notify_deadline_25_webpush_pu = Notify(type='deadline_25', method='webpush', time=date_deadline_25_percent,
                                                  id_recipient=self.id_partner_user, id_task=self.task.id)
            notify_deadline_25_email_pu = Notify(type='deadline_25', method='email', time=date_deadline_25_percent,
                                                 id_recipient=self.id_partner_user, id_task=self.task.id)
            db.session.add(notify_deadline_25_webpush_cu)
            db.session.add(notify_deadline_25_email_cu)
            db.session.add(notify_deadline_25_webpush_pu)
            db.session.add(notify_deadline_25_email_pu)

        if datetime.now() < date_deadline_50_percent:
            notify_deadline_50_webpush_cu = Notify(type='deadline_50', method='webpush', time=date_deadline_50_percent,
                                               id_recipient=self.id_current_user, id_task=self.task.id)
            notify_deadline_50_email_cu = Notify(type='deadline_50', method='email', time=date_deadline_50_percent,
                                              id_recipient=self.id_current_user, id_task=self.task.id)
            notify_deadline_50_webpush_pu = Notify(type='deadline_50', method='webpush', time=date_deadline_50_percent,
                                                  id_recipient=self.id_partner_user, id_task=self.task.id)
            notify_deadline_50_email_pu = Notify(type='deadline_50', method='email', time=date_deadline_50_percent,
                                                 id_recipient=self.id_partner_user, id_task=self.task.id)
            db.session.add(notify_deadline_50_webpush_cu)
            db.session.add(notify_deadline_50_email_cu)
            db.session.add(notify_deadline_50_webpush_pu)
            db.session.add(notify_deadline_50_email_pu)

        if datetime.now() < date_deadline_75_percent:
            notify_deadline_75_webpush_cu = Notify(type='deadline_75', method='webpush', time=date_deadline_75_percent,
                                               id_recipient=self.id_current_user, id_task=self.task.id)
            notify_deadline_75_email_cu = Notify(type='deadline_75', method='email', time=date_deadline_75_percent,
                                              id_recipient=self.id_current_user, id_task=self.task.id)
            notify_deadline_75_webpush_pu = Notify(type='deadline_75', method='webpush', time=date_deadline_75_percent,
                                                   id_recipient=self.id_partner_user, id_task=self.task.id)
            notify_deadline_75_email_pu = Notify(type='deadline_75', method='email', time=date_deadline_75_percent,
                                                 id_recipient=self.id_partner_user, id_task=self.task.id)
            db.session.add(notify_deadline_75_webpush_cu)
            db.session.add(notify_deadline_75_email_cu)
            db.session.add(notify_deadline_75_webpush_pu)
            db.session.add(notify_deadline_75_email_pu)

        if datetime.now() < self.task.deadline:
            notify_deadline_100_webpush_cu = Notify(type='deadline_100', method='webpush', time=self.task.deadline,
                                                id_recipient=self.id_current_user, id_task=self.task.id)
            notify_deadline_100_email_cu = Notify(type='deadline_100', method='email', time=self.task.deadline,
                                               id_recipient=self.id_current_user, id_task=self.task.id)
            notify_deadline_100_webpush_pu = Notify(type='deadline_100', method='webpush', time=self.task.deadline,
                                                    id_recipient=self.id_partner_user, id_task=self.task.id)
            notify_deadline_100_email_pu = Notify(type='deadline_100', method='email', time=self.task.deadline,
                                                  id_recipient=self.id_partner_user, id_task=self.task.id)
            db.session.add(notify_deadline_100_webpush_cu)
            db.session.add(notify_deadline_100_email_cu)
            db.session.add(notify_deadline_100_webpush_pu)
            db.session.add(notify_deadline_100_email_pu)

        db.session.commit()

    def delete_notify(self):
        arr_notify = Notify.query.filter_by(id_task=self.task.id).all()
        if arr_notify is not None:
            for notify in arr_notify:
                db.session.delete(notify)
                db.session.commit()

    def update_notify(self):
        self.delete_notify()
        self.add_notify()

    def update_task_deadline_by_notify(self, type_notify):
        if type_notify == 'deadline_25':
            self.task.deadline_25_percent = 't'
        if type_notify == 'deadline_50':
            self.task.deadline_50_percent = 't'
        if type_notify == 'deadline_75':
            self.task.deadline_75_percent = 't'
        if type_notify == 'deadline_100':
            self.task.deadline_100_percent = 't'

    def get_text_notify(self, notify_time):
        remains_days = int((self.task.deadline - notify_time).total_seconds() / 60 / 60 / 24)
        if remains_days >= 1:
            return 'Остался(-ось) ' + str(remains_days) + ' день(дней) на ' + 'выполнение задачи ' + self.task.title
        else:
            return 'На выполнение задачи ' + self.task.title + ' осталось меньше 24 часов'

    def send_webpush_by_user(self, data_push, arr_subscr_by_user):
        for subscr_by_user in arr_subscr_by_user:
            push_param = json.loads((subscr_by_user.push_param).replace('\'', '\"').replace("None", "\"\""))
            try:
                webpush(
                    subscription_info=push_param,
                    data=data_push,
                    vapid_private_key='./private_key.pem',
                    vapid_claims={
                        'sub': 'mailto:{}'.format(app.config['ADMINS'][0])
                    }
                )
            except WebPushException as ex:
                print('I can\'t do that: {}'.format(repr(ex)))
                print(ex)
                if ex.response.status_code == 410:
                    print('subscr 410 error', subscr_by_user.id_users, subscr_by_user.push_param)
                    # если срок действия подписки истек, то удаляем её из базы
                    db.session.delete(subscr_by_user)
                    db.session.commit()
                # Mozilla returns additional information in the body of the response.
                if ex.response and ex.response.json():
                    extra = ex.response.json()
                    print('Remote service replied with a {}:{}, {}',
                          extra.code,
                          extra.errno,
                          extra.message)
    def send_webpush(self, text_notify, id_recipient):
        #отправляем оповещение сначала инициатору задачи, а потом его партнеру
        data_push = json.dumps({
            'title': 'Внимание!',
            'body': text_notify
        })

        arr_subscr_by_user = Subscription.query.filter_by(id_users=id_recipient).all()
        if arr_subscr_by_user is not None:
            self.send_webpush_by_user(data_push, arr_subscr_by_user)
    def send_webpush_notify(self):
        arr_webpush_notify = Notify.query.filter_by(method='webpush', id_task=self.task.id).all()
        if arr_webpush_notify is not None:
            for webpush_notify in arr_webpush_notify:
                if datetime.strptime(webpush_notify.time.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S') < \
                        datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'):
                    text_notify = self.get_text_notify(webpush_notify.time)
                    self.send_webpush(text_notify, webpush_notify.id_recipient)
                    self.update_task_deadline_by_notify(webpush_notify.type)
                    db.session.delete(webpush_notify)
                    db.session.commit()
    def send_email_notify(self):
        arr_email_notify = Notify.query.filter_by(method='email', id_task=self.task.id).all()
        if arr_email_notify is not None:
            for email_notify in arr_email_notify:
                if datetime.strptime(email_notify.time.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S') < \
                        datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'):
                    text_notify = self.get_text_notify(email_notify.time)

                    if email_notify.id_recipient == self.id_current_user:
                        if self.is_send_email_current_user != 'f':
                            send_email('Внимание!',
                                       sender=app.config['ADMINS'][0],
                                       recipients=[self.email_current_user],
                                       text_body=text_notify,
                                       html_body=""
                                       )
                        self.update_task_deadline_by_notify(email_notify.type)
                        db.session.delete(email_notify)
                        db.session.commit()

                    if email_notify.id_recipient == self.id_partner_user:
                        if self.is_send_email_partner_user != 'f':
                            send_email('Внимание!',
                                       sender=app.config['ADMINS'][0],
                                       recipients=[self.email_partner_user],
                                       text_body=text_notify,
                                       html_body=""
                                       )
                        self.update_task_deadline_by_notify(email_notify.type)
                        db.session.delete(email_notify)
                        db.session.commit()
