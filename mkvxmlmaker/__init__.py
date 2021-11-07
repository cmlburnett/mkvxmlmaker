"""
Helper classes to aide in embedding chapter and tag information into an MKV file.
Use the mkvmerge(1) tool to combine one or both of these XML files into an MKV file.

Uses crudexml, a simple XML library I wrote
"""

from crudexml import node, tnode, dnode, docroot

import os
import subprocess
import xml.etree.ElementTree as ET

__all__ = ["MKVXML_chapter", "MKVXML_tags", "sec_str", "t_to_sec"]


def sec_str(sec):
	"""
	Convert integer seconds to HHH:MM:SS formatted string
	Returns as HHH:MM:SS, MM:SS, or 0:SS with zero padding except for the most significant position.
	"""

	min,sec = divmod(sec, 60)
	hr,min = divmod(min, 60)

	if hr > 0:
		return "%d:%02d:%06.03f" % (hr,min,sec)
	elif min > 0:
		return "%d:%06.03f" % (min,sec)
	else:
		return "0:%06.03f" % sec

def t_to_sec(t):
	"""
	Convert a time spec (HHH:MM:SS) into an float number of seconds.
	"""

	if '.' in t:
		parts = t.split('.')
		t = parts[0]
		frac = float('.' + parts[1])
	else:
		frac = 0.0

	parts = t.split(':')
	if len(parts) == 1:
		return int(parts[0]) + frac
	elif len(parts) == 2:
		return int(parts[0])*60 + int(parts[1]) + frac
	elif len(parts) == 3:
		return int(parts[0])*3600 + int(parts[1])*60 + int(parts[2]) + frac
	else:
		raise ValueError("Too many parts to time format: '%s'" % t)

class MKVXML_chapter:
	_chapters = None

	def __init__(self):
		self._chapters = []

	@property
	def Chapters(self):
		return self._chapters

	def AddChapter(self, lengthfancy, title, num=None):
		"""Add a chapter to the list"""

		if num is None:
			num = len(self._chapters)+1
		d = {'num': num, 'lengthfancy': lengthfancy, 'title': title}
		self._chapters.append(d)

	@staticmethod
	def FromMKV(fname):
		"""
		Using mkvinfo(1), extract chapter information from an MKV file.
		Output of mkvinfo is indented using a + character.
		Parse the output looking for level of ident of + and make a recursive structure of all metadata.
		Each entry is (indent, value, children) where indent is an int, value is whatever the metadata
		 value that mkvinfo spits out, and children is a list of the same 3-tuples.

		The chapters are found under 'Segment: XXXXX' > 'Chapters' > 'Edition entry'.
		Under this are
		 'Chapter atom' entries with 'Chapter start time: XXXXXX',
		 'Chapter track' > 'Chapter track number: XX',
		 and 'Chapter display' > 'Chapter string: XXXX'
		These three values are extracted and supplied to MKVXML_chapter.AddChapter().

		Returned is an MKVXML_chapter instance.
		"""
		if not os.path.exists(fname):
			raise FileNotFound("Cannot get chapter info from file '%s', file not found" % fname)

		# Run mkvinfo and parse the output by line
		ret = subprocess.run(['mkvinfo', fname], stdout=subprocess.PIPE)
		out = ret.stdout.decode('utf8')
		lines = out.split('\n')

		# Keep a running list of tuples to add children to
		parents = []
		# Processed output of root tuples with indent == 0
		proc = []
		for line in lines:
			# Weed out empty lines
			line = line.strip()
			if not len(line): continue

			# Column (ie, the index) of the + indicats the indent level
			idx = line.index('+')
			# Get the rest of the line "|+ Chapters" becomes idx == 2 and x == "Chapters"
			x = (idx, line[idx+1:].strip(), [])

			# If root object, just add it
			if idx == 0:
				proc.append(x)

			# If there are no parents (ie, first line) add to parents
			if len(parents) == 0:
				parents.append(x)

			# There are parents so need to make sure current line is added to the correct level
			else:
				# Difference between parent level and current line indent
				delta = idx - (len(parents) - 1)

				# If at the same level, then this line is at the same level therefore is a sibling to parent[-1]
				if delta == 0:
					# Found sibling

					# Pop off sibling
					parents.pop()
					# Add current as the next child
					parents[-1][2].append(x)
					# Add current line as new parent
					parents.append(x)

				elif delta == 1:
					# Found a child of the parent
					parents[-1][2].append(x)
					parents.append(x)

				elif delta > 1:
					# Jumped from like indent 2 to 4
					raise Exception("Found a jump in file '%s' from indent %d to %d: %s" % (fname, len(parents), idx, line))

				elif delta < 0:
					# current line is not under the current parent, so have to back up the chain

					# Trim down parents
					parents = parents[:(delta-1)]
					# If parents is empty then adding a new root level (ie, indent == 0) tuple

					if not len(parents):
						parents.append(x)
					else:
						# Add to parent's children
						parents[-1][2].append(x)

					# Set current as new parent
					parents.append(x)
				else:
					raise NotImplementedError("Shouldn't reach this spot")

		# Create object to return
		ret = MKVXML_chapter()

		# Parse down through the tree and find chapters
		for step in proc:
			if step[1].startswith('Segment:'):
				for substep in step[2]:
					if substep[1] == 'Chapters':
						editionentry = substep[2][0]
						chapters = editionentry[2]

						for chap in chapters:
							if chap[1] != 'Chapter atom': continue

							num = None
							title = None
							start = None
							for subchap in chap[2]:
								if subchap[1].startswith('Chapter time start'):
									start = subchap[1].split(': ',1)[-1]
								elif subchap[1] == 'Chapter track':
									subsubchap = subchap[2][0]
									if subsubchap[1].startswith('Chapter track number'):
										num = subsubchap[1].split(': ',1)[-1]
								elif subchap[1] == 'Chapter display':
									subsubchap = subchap[2][0]
									if subsubchap[1].startswith('Chapter string'):
										title = subsubchap[1].split(': ',1)[-1]

							# Should have found all three
							if num is None:
								print(chap)
								raise Exception("Chapter has no number")
							if title is None:
								print(chap)
								raise Exception("Chapter has no title")
							if start is None:
								print(chap)
								raise Exception("Chapter has no start time")

							# Add chapter
							ret.AddChapter(start, title, num)

						return ret

		raise Exception("Unable to find chapters")

	@staticmethod
	def FromXml(fname):
		c = MKVXML_chapter()

		tree = ET.parse(fname)
		for e in tree.iter('ChapterAtom'):
			l = e.find('ChapterTimeStart').text
			title = e.find('ChapterDisplay').find('ChapterString').text
			num = e.find('ChapterTrack').find('ChapterTrackNumber').text
			c.AddChapter(l, title, num)

		return c

	def ToXml(self):
		"""
		Output chapters as XML document in a format it expects.
		"""
		doc = docroot()

		doc.AddChild( dnode('Chapters', 'matroskachapters.dtd') )
		root = doc.AddChild( node('Chapters') )

		ee = root.AddChild( node('EditionEntry') )

		for chap in self._chapters:
			ca = ee.AddChild( node('ChapterAtom') )
			ct = ca.AddChild( node('ChapterTrack') )
			ct.AddChild( tnode('ChapterTrackNumber', chap['num']) )

			ca.AddChild( tnode('ChapterTimeStart', chap['lengthfancy']) )

			cd = ca.AddChild( node('ChapterDisplay') )
			cd.AddChild( tnode('ChapterString', chap['title']) )
			cd.AddChild( tnode('ChapterLanguage', 'eng') )

		# Prefix content with fancy headers
		return doc.OuterXMLPretty

	def Save(self, path):
		"""Save chapter information to a file as XML."""

		xml = self.ToXml()

		with open(path, 'w') as f:
			f.write(xml)

class MKVXML_tags:
	_tags = None
	_simples = None

	class Tag:
		_targettype = None
		_targettypevalue = None
		_simples = None

		_attachmentuids = None
		_chapteruids = None
		_editionuids = None
		_trackuids = None

		def __init__(self):
			self._targettype = None
			self._targettypevalue = None
			self._simples = {}

			self._attachmentuids = []
			self._chapteruids = []
			self._editionuids = []
			self._trackuids = []

		@property
		def TargetType(self):
			return self._targettype
		@TargetType.setter
		def TargetType(self, val):
			self._targettype = val

		@property
		def TargetTypeValue(self):
			return self._targettypevalue
		@TargetTypeValue.setter
		def TargetTypeValue(self, val):
			self._targettypevalue = val

		@property
		def Simples(self):
			return dict(self._simples)

		def __getitem__(self, k):
			return self._simples[k]

		def __setitem__(self, k,v):
			self._simples[k] = v


		def AddAttachmentUID(self, uid):
			self._attachmentuids.append(uid)
		@property
		def AttachmentUIDs(self):
			return tuple(self._attachmentuids)

		def AddChapterUID(self, uid):
			self._chapteruids.append(uid)
		@property
		def ChapterUIDs(self):
			return tuple(self._chapteruids)

		def AddEditionUID(self, uid):
			self._editionuids.append(uid)
		@property
		def EditionUIDs(self):
			return tuple(self._editionuids)

		def AddTrackUID(self, uid):
			self._trackuids.append(uid)
		@property
		def TrackUIDs(self):
			return tuple(self._trackuids)

	def __init__(self):
		self._tags = []
	
	def NewTag(self):
		t = MKVXML_tags.Tag()
		self._tags.append(t)
		return t

	def ToXml(self):
		doc = docroot()

		doc.AddChild( dnode('Tags', 'matroskatags.dtd') )
		root = doc.AddChild( node('Tags') )

		for tag in self._tags:
			t = root.AddChild( node('Tag') )
			tt = t.AddChild( node('Targets') )

			for uid in tag.AttachmentUIDs:	tt.AddChild( tnode("AttachmentUID", uid) )
			for uid in tag.ChapterUIDs:		tt.AddChild( tnode("ChapterUID", uid) )
			for uid in tag.EditionUIDs:		tt.AddChild( tnode("EditionUID", uid) )
			for uid in tag.TrackUIDs:		tt.AddChild( tnode("TrackUID", uid) )

			if tag.TargetType:
				ttt = tt.AddChild( tnode('TargetType', tag.TargetType) )
			if tag.TargetTypeValue:
				ttv = tt.AddChild( tnode('TargetTypeValue', tag.TargetTypeValue) )

			for k in sorted(tag.Simples.keys()):
				v = tag.Simples[k]

				s = t.AddChild( node('Simple') )
				s.AddChild( tnode('Name', k) )
				s.AddChild( tnode('String', v) )
				s.AddChild( tnode('TagLanguage', 'eng') ) # XXX: assumed
				

		return doc.OuterXMLPretty

	def Save(self, path):
		xml = self.ToXml()

		with open(path, 'w') as f:
			f.write(xml)

