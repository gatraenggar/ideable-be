import pika

def send_invitation_email(recipient_email, auth_token):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    channel.exchange_declare(exchange='service_logs', exchange_type='direct')

    message = recipient_email + ' ' + auth_token
    channel.basic_publish(
        exchange='service_logs',
        routing_key='workspace_invitation',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode = 2,
        )
    )

    print(" [x] Sent %r" % recipient_email)
    connection.close()
