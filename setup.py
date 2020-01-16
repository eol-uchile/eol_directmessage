import setuptools

setuptools.setup(
    name="eol_directmessage",
    version="0.0.1",
    author="matiassalinas",
    author_email="matsalinas@uchile.cl",
    description="Eol direct message",
    long_description="Eol direct message",
    url="https://eol.uchile.cl",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "lms.djangoapp": [
            "eol_directmessage = eol_directmessage.apps:EolDirectMessageConfig",
        ],
        "openedx.course_tab": [
            "eol_directmessage = eol_directmessage.plugins:EolDirectMessageTab",
        ]
    },
)
