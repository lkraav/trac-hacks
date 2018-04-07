from setuptools import setup

setup(
    name='TracTicketValidator',
    version='0.3',
    author='Richard Liao',
    author_email='richard.liao.i@gmail.com',
    maintainer='Richard Liao',
    maintainer_email='richard.liao.i@gmail.com',
    description="Ticket validator plugin for Trac.",
    license='BSD',
    keywords='trac ticket validator',
    url='https://trac-hacks.org/wiki/TracTicketValidatorPlugin',
    packages=['tracticketvalidator'],
    package_data={
        'tracticketvalidator': ['*.txt']
    },
    classifiers=[
        'Framework :: Trac',
    ],
    install_requires=['Trac'],
    entry_points={
        'trac.plugins': [
            'tracticketvalidator = tracticketvalidator.ticketvalidator'
        ]
    },
)
