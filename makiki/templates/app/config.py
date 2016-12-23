# -*- coding: utf-8 -*-

DATABASE_CONFIG = {
    'host': 'db',
    'port': '5432',
    'user': 'postgres',
    'password': 'postgres',
    'database': 'postgres',
}

LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'generic': {
            'format': '%(asctime)s [%(process)d] [%(levelname)s] %(name)s: %(message)s',
        },
        'verbose': {
            'format': '[%(process)s][%(levelname)s][%(module)s-%(lineno)d]%(asctime)s %(name)s:%(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'generic',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}
