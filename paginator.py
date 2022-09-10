import datetime, markdown, os, re


def fwrite(filename, text):
	"""Write content to file and close the file."""
	basedir = os.path.dirname(filename)
	if not os.path.isdir(basedir):
		os.makedirs(basedir)
	with open(filename, 'wb') as f:
		f.write(text.encode('utf8'))


class Page(object):
	
	def __init__(self, env, config, template_name):
		date_slug = os.path.basename(template_name).split('.')[0]
		match = re.search(r'^(?:(\d\d\d\d-\d\d-\d\d)-)?(.+)$', date_slug)
		date_str = match.group(1) or '1970-01-01'
		
		self.name = template_name
		self.date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
		self.permalink = match.group(2)
		self._filename = ''
		self._permalink = ''
		self._template = env.get_template(template_name)
		self._config = config
		self._env = env
		self._vars = {
			'site': config['site'],
			'page': self
		}
		self.render()


	def render(self, more_vars = {}):
		self._vars.update(more_vars)
		# There a better way?
		self._vars.update(self._template.make_module(self._vars).__dict__)

		# Convert Markdown to HTML and render the specified layout.
		if self.name.endswith('.md'):
			md = markdown.Markdown(extensions=['fenced_code','meta','codehilite'])
			self._vars['content'] = md.convert(self._template.render(self._vars))
			meta = self.process_meta(md.Meta)
			self._vars.update(meta)
			layout = self._vars.get('layout', '')
			if layout != '':
				t = self._env.get_template(layout)
				if 'content' in meta:
					print('  Warning: Defined variable "content" is not allowed with "layout".')
				self.url = self.get_permalink()
				self._vars['output'] = t.render(self._vars)
		else:
			self.url = self.get_permalink()
			self._vars['output'] = self._template.render(self._vars)
			
	def get(self, key, default):
		return self._vars.get(key, default)
		
	def __getattribute__(self, name):
		if name != '_vars' and name in self._vars:
			return self._vars[name]
		return super(Page, self).__getattribute__(name)
		

	def process_meta(self, d):
		r = {}
		for k, v in d.items():
			r[k] = v[1:] if len(v) > 1 else v[0]
		return r

	def get_permalink(self, use_cache = True):
		if use_cache and self._permalink != '':
			return self._permalink
		elif self.name == 'index.html':
			self._permalink = '/'
		elif self.name.endswith('.xml'):
			self._permalink = '/' + self.name
		else:
			url = getattr(self, 'permalink', '')
			if url == '':
				self._permalink = '/' + self.name[:self.name.rfind('.')]
			elif url.startswith('/'):
				self._permalink = url
			else:
				# Permalinks are relative if they don't start with '/'
				d = os.path.dirname(self.name)
				self._permalink = '/' + os.path.join(d, url)
		return self._permalink
		
	def get_filename(self, use_cache = True):
		if use_cache and self._filename != '':
			return self._filename
		
		path = self.get_permalink(use_cache)
		if path.startswith('/'):
			path = path.lstrip('/')

		# XML files retain their filename, ignore permalink
		if self.name.endswith('.xml'):
			self._filename = os.path.join(self._config['output_dir'], self.name)
		else:
			self._filename = os.path.join(self._config['output_dir'], path, 'index.html')
			
		return self._filename

		
	def save(self, filename = ''):
		if filename == '':
			filename = self.get_filename()
		fwrite(filename, self.get('output', ''))


class Paginator(object):
	
	def __init__(self, env, config, page, posts):
		self.permalink = config['paginator']['permalink']
		self.first_permalink = page.get_permalink()
		
		# Sort by date
		posts.sort(key = lambda x:x.date, reverse=True)

		items_per_page = config['paginator']['items_per_page']
		template_name = page.name
		self.pages = []
		self.all_posts = posts
		self.page_count = 1 + int((len(posts) - 1) / items_per_page)
		
		for i in range(1, self.page_count + 1):
			start = (i - 1) * items_per_page
			end = i * items_per_page
			self.posts = posts[start:end]
			print('  Doing page {} of {}'.format(i, self.page_count))

			page = Page(env, config, template_name)
			self.page = i
			self.prev_permalink = ''
			self.next_permalink = ''
			if i > 1:
				page.permalink = self.permalink.replace(':num', str(i))
				if i == 2:
					self.prev_permalink = self.first_permalink
				else:
					self.prev_permalink = self.permalink.replace(':num', str(i-1))
			if i < self.page_count:
				self.next_permalink = self.permalink.replace(':num', str(i+1))
			
			page.render({'paginator': self})
			self.pages.append(page)
		
	def get_pages(self):
		return self.pages
