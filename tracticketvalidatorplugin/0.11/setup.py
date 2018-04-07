from setuptools import find_packages, setup

setup(
    name='TracTicketValidator',
    version='0.2',
    author='Richard Liao',
    author_email='richard.liao.i@gmail.com',
    maintainer='Richard Liao',
    maintainer_email='richard.liao.i@gmail.com',
    description="Ticket validator plugin for Trac.",
    license='BSD',
    keywords='trac ticket validator',
    url='https://trac-hacks.org/wiki/TracTicketValidatorPlugin',
    packages=['ticketvalidator'],
    package_data={
        'ticketvalidator': ['*.txt']
    },
    classifiers=[
        'Framework :: Trac',
    ],
    install_requires=['Trac'],
    entry_points={
        'trac.plugins': [
            'tracticketvalidator = ticketvalidator.ticketvalidator'
        ]
    },
)
