from distutils.core import setup

majv = 1
minv = 0

setup(
	name = 'mkvxmlmaker',
	version = "%d.%d" %(majv,minv),
	description = "Python module to make the XML files for mkvmerge utility",
	author = "Colin ML Burnett",
	author_email = "cmlburnett@gmail.com",
	url = "",
	packages = ['mkvxmlmaker'],
	package_data = {'mkvxmlmaker': ['mkvxmlmaker/__init__.py']},
	classifiers = [
		'Programming Language :: Python :: 3.4'
	]
)
