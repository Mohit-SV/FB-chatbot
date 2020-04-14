bind = '0.0.0.0:8000'
backlog = 1024
workers = 5
worker_class = 'gevent'
worker_connections = 1000
timeout = 30
keepalive = 2
spew = False

errorlog = '/home/ec2-user/www/upwards-growth-projects/fb_msg_bot/fb_msg_bot/logs/error.log'
loglevel = 'info'
accesslog = '/home/ec2-user/www/upwards-growth-projects/fb_msg_bot/fb_msg_bot/logs/access.log'
access_log_format = "RemoteAddress: %(h)s %(l)s UserName: %(u)s ** Date: %(t)s ** StatusLine: %(r)s ** StatusCode: %(s)s ** ResponseLength: %(b)s ** Referer: %(f)s ** UserAgent: %(a)s ** ResponseTime: %(L)s ** QueryString: %(q)s "
