import pika

def send_confirmation_email(recipient_email, auth_token):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    channel.exchange_declare(exchange='email_confirmation', exchange_type='direct')

    message = recipient_email + ' ' + auth_token
    channel.basic_publish(
        exchange='email_confirmation',
        routing_key='email_confirmation',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode = 2,
        )
    )

    print(" [x] Sent %r" % recipient_email)
    connection.close()
