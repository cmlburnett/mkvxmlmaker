"""
"""

from crudexml import node, tnode, dnode, docroot

__all__ = ["MKVXML_chapter", "MKVXML_tags"]

class MKVXML_chapter:
	_chapters = None

	def __init__(self):
		self._chapters = []

	def AddChapter(self, lengthfancy, title):
		d = {'num': (len(self._chapters)+1), 'lengthfancy': lengthfancy, 'title': title}
		self._chapters.append(d)

	def ToXml(self):
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

