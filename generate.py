#!/usr/bin/env python
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import datetime, json, markdown, os, shutil, sys
import paginator


# Default configuration.
config = {
	'base_path': '',
	'app_name': 'app',
	'output_dir': 'html',
	'static_dir': 'static',
	'blog_dir': 'blog',
	'paginator': {
		'posts_path': 'posts',
		'permalink': '/news/:num/',
		'items_per_page': 10,
		'layout': 'layout/post.tmpl'
	},
	'site': {
		'domain': 'http://site.com',
		'base_url': ''
	}
}


def fread(filename):
	"""Read file and close the file."""
	with open(filename, 'r') as f:
		return f.read()


def process_meta(d):
	r = {}
	for k, v in d.items():
		r[k] = v[1:] if len(v) > 1 else v[0]
	return r

	
def filter_date(value, format = '%m-%d-%Y'):
	return value.strftime(format)


def filter_date_to_xmlschema(value):
	return ""

	
def filter_xml_escape(s):
	return s


def purge():
	# Create a new site directory from scratch.
	d = config['output_dir']
	if os.path.isdir(d):
		shutil.rmtree(d)
	shutil.copytree(config['static_dir'], d)


def main(config_name = ''):
	config_filename = 'config.json'
	if config_name != '':
		config_filename = 'config_'+config_name+'.json'
	if os.path.isfile(config_filename):
		config.update(json.loads(fread(config_filename)))
	root = os.path.dirname(os.path.abspath(__file__))

	purge()

	env = Environment(loader = FileSystemLoader(config['app_name']))
	env.filters['date'] = filter_date
	env.filters['xml_escape'] = filter_xml_escape
	env.filters['date_to_xmlschema'] = filter_date_to_xmlschema

	config['site']['debug'] = (config_name == 'debug')
	config['site']['posts'] = []
	
	page_templates = []
	pages = []
	posts = []
	posts_path = config['paginator']['posts_path']


	templates = env.list_templates(extensions = ['html','xml','md'])

	# Loop through templates to find those in `path`
	for template_name in templates:
		path = os.path.dirname(template_name)
		if path != posts_path:
			page_templates.append(template_name)
		else:
			post = paginator.Page(env, config, template_name)
			posts.append(post)

	config['site']['posts'] = posts
	
	for template_name in page_templates:
		page = paginator.Page(env, config, template_name)
		if page.get('paginate', False):
			p = paginator.Paginator(env, config, page, posts)
			pages.extend(p.get_pages())
		else:
			pages.append(page)
	
	for page in posts + pages:
		print(page.name, page.url)
		print(page.get_filename())
		page.save()

if __name__ == '__main__':
	config_name = ''
	if len(sys.argv) > 1:
		config_name = sys.argv[1]
	main(config_name)
