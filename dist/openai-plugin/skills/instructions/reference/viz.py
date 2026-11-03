# Copyright (c) 2001-2024 WorldViz.
# All rights reserved.
#############################################################
# Vizard Python API
#############################################################
import os

try:
	import _vizcore
except ImportError:
	if 'VIZARD_WORKER_PROCESS' in os.environ:
		def _dummy(*args,**kw):
			return None
		_ipcSend = _dummy
		_ipcSendEx = _dummy
	else:
		raise ImportError('viz module can only be imported by Vizard')
else:
	_ipcSend = _vizcore._ipcSend
	_ipcSendEx = _vizcore._ipcSendEx

import io
import sys
import math
import mmap
import types
import random
import vizmat
import pickle
import warnings
import builtins
from vizutil import *

############################################
###### Initialize Python environment #######
############################################

#Set viz.args for backwards compatibility
args = sys.argv[1:]

#Fixes problems with some 3rd party libraries
if not 'HOME' in os.environ:
	os.environ['HOME'] = os.environ['USERPROFILE']

#Override builtin input methods with Vizard input methods
def input(prompt=''):
	"""Same behavior as builtin input command, but uses popup window"""
	import vizinput
	return eval(vizinput.input(prompt,''))

def raw_input(prompt=''):
	"""Same behavior as builtin raw_input command, but uses popup window"""
	import vizinput
	return vizinput.input(prompt,'')

# Override input function for Vizard scripts
if 'VIZARD_SCRIPT_PROCESS' in os.environ:
	builtins.input = raw_input

############################################
############## IPC functions ###############
############################################

def _ipcSendCallback(event, function, mode, classID, priority):
	return _ipcSendEx( 1 , (event,function,mode,classID,priority) )

def _ipcSendDirector(function, args, kw, pool):
	return _ipcSendEx( 2 , (function, args, kw, pool) )

def _ipcSendCustomEvent(event,args):
	return _ipcSendEx( 3 , (event,args) )

def _ipcSendCameraHandler(handler):
	return _ipcSendEx( 4 , (handler,) )

def _ipcSendPostEvent(event,args):
	return _ipcSendEx( 6 , (event,args) )

def _ipcSendPostFunctionCall(func,args,kw):
	return _ipcSendEx( 7 , (func,args,kw) )

def _ipcSendFunctionCall(func,args,kw):
	return _ipcSendEx( 14 , (func,args,kw) )

def _ipcSendAddTargetCallback(object_id, object_type, event, func, priority):
	return _ipcSendEx( 9 , (object_id, object_type, event, WeakMethod(func), priority) )

def _ipcSendRemoveTargetCallback(object_id, object_type, event, func):
	return _ipcSendEx( 10 , (object_id, object_type, event, WeakMethod(func)) )

def _ipcSendTargetEvent(object_id, object_type, event, args):
	return _ipcSendEx( 11 , (object_id, object_type, event, args) )

def _ipcLaunchVizconnect():
	vc = sys.modules.get('vizconnect',None)
	if vc is None:
		import subprocess
		subprocess.Popen([sys.executable,os.path.join(sys.exec_prefix,'Scripts','vizconnect_interface.py')])
	else:
		vc.interface.go(None)

############################################
############# Plugin functions #############
############################################

def upgradeClass(obj, name, method, override=False):
	"""Upgrade a class 'obj' by adding a method named 'name' which will call 'method'"""
	if override or not hasattr(obj,name):
		setattr(obj, name, method)

def upgradeInstance(obj, name, method, override=False):
	"""Upgrade an 'obj' by adding a method named 'name' which will call 'method'"""
	if override or not hasattr(obj,name):
		setattr(obj, name, types.MethodType(method, obj))

def upgradeModule(module, name, obj, override=False):
	"""Upgrade a 'module' by adding an object 'obj' named 'name'"""
	if override or not hasattr(module,name):
		setattr(module, name, obj)

__SensorClass = {}
def upgradeSensor(filename,newClass):
	"""Register a class that will be used with all sensors with the given filename"""
	__SensorClass[filename.lower()] = newClass

def createSensor(filename,id):
	"""Create a sensor with the given filename and id
	@return VizSensor()"""
	return __SensorClass.get(filename.lower(),VizSensor)(id)

__CustomNodeClass = {}
def upgradeCustomNode(filename,newClass):
	"""Register a class that will be used with all custom nodes with the given filename"""
	__CustomNodeClass[filename.lower()] = newClass

def createCustomNode(filename,id,**kw):
	"""Create a custom node with the given filename and id
	@return VizCustomChild()"""
	return __CustomNodeClass.get(filename.lower(),VizCustomChild)(id,**kw)

__ImageGenClass = {}
def upgradeImageGen(filename,newClass):
	"""Register a class that will be used with all imagegens with the given filename"""
	__ImageGenClass[filename.lower()] = newClass

def createImageGen(filename,id):
	"""Create an imagegen with the given filename and id
	@return VizImageGen()"""
	return __ImageGenClass.get(filename.lower(),VizImageGen)(id)

__ModifierClass = {}
def upgradeModifier(filename,newClass):
	"""Register a class that will be used with all modifiers with the given filename"""
	__ModifierClass[filename.lower()] = newClass

def createModifier(filename,id):
	"""Create a modifier with the given filename and id
	@return VizModifier()"""
	return __ModifierClass.get(filename.lower(),VizModifier)(id)

_newExtensionClass = None
_newExtensionFilename = ''
def _beginAddExtension(filename):
	global _newExtensionClass, _newExtensionFilename
	_newExtensionClass = None
	_newExtensionFilename = filename

def _endAddExtension():
	global _newExtensionClass, _newExtensionFilename
	_newExtensionClass = None
	_newExtensionFilename = ''

def _addExtensionCodeToCache(filename,code):
	"""Add code to extension cache for completion support"""

	# Only cache code if process was launched by Vizard IDE
	if not ('VIZARD_LAUNCHED_FROM_IDE' in os.environ and 'VIZARD_LOCAL_APPDATA' in os.environ):
		return

	# Don't cache code while publishing
	if getOption('viz.publishing',0,type=int):
		return

	# Get full path to extension
	ext_path = res.getFullPath(filename)
	if not ext_path or not os.path.isfile(ext_path):
		return

	# Get full path to cache directory and file
	base_name = os.path.basename(ext_path)
	cache_path = os.path.join(os.environ['VIZARD_LOCAL_APPDATA'],'code_cache')
	cache_file = os.path.join(cache_path,base_name+'.py')

	# Check if new cache file needs to be created
	if os.path.isfile(cache_file):
		modified_diff = abs(os.path.getmtime(ext_path)-os.path.getmtime(cache_file))
		if modified_diff <= 0.001:
			return

	else: # Otherwise, ensure directory is created
		try:
			os.makedirs(cache_path)
		except OSError:
			pass

	# Write extension code to cache file
	try:
		with open(cache_file,'w') as f:
			f.write(code)
		import shutil
		shutil.copystat(ext_path,cache_file)
	except (IOError,OSError):
		pass

def _runExtensionCode(code):
	"""Run code to initialize extension"""

	# Prepend viz module import
	code = 'import viz\n' + code

	# Execute code in private namespace
	d = {}
	exec(code, d)

	# If extension class was not registered, then automatically register first encountered extension subclass
	if _newExtensionClass is None:
		for obj in d.values():
			if isinstance(obj,type) and issubclass(obj,VizExtension):
				setExtensionClass(obj)
				break

	# Add code to extension code cache for auto completion support
	if _newExtensionFilename:
		module_doc = '"""\n%s Python interface.\nThis file was automatically generated and should not be modified.\n"""\n' % (_newExtensionFilename)
		code = module_doc + code
		_addExtensionCodeToCache(_newExtensionFilename,code)

	return _newExtensionClass

def setExtensionClass(extClass):
	"""Should be called within extension plugin to set the class for the new extension"""
	global _newExtensionClass
	_newExtensionClass = extClass

def createExtension(filename, id, cls=None):
	"""Create an extension with the given filename and id
	@return VizExtension()"""
	defaultClass = cls
	if defaultClass is None:
		defaultClass = _newExtensionClass
	if defaultClass is None:
		defaultClass = VizExtension
	return defaultClass._GetObject(id)

################################################################################################
################################################################################################
#							      Utility Functions/Classes									   #
################################################################################################
################################################################################################

def _getFileExtension(filename):
	return filename.rsplit('.',1)[-1]

_islist = islist

class RenderStats(object):
	def __init__(self,frameTime,updateTime,cullTime,drawTime,swapTime,gpuTime,effectComposeTime,primitiveCount,drawableCount,systemMemory,gpuMemory):
		self.frameTime = frameTime
		self.updateTime = updateTime
		self.cullTime = cullTime
		self.drawTime = drawTime
		self.swapTime = swapTime
		self.gpuTime = gpuTime
		self.effectComposeTime = effectComposeTime
		self.primitiveCount = primitiveCount
		self.drawableCount = drawableCount
		self.systemMemory = systemMemory
		self.gpuMemory = gpuMemory

	def __repr__(self):
		return """RenderStats(
	frameTime = {frameTime:,}
	updateTime = {updateTime:,}
	cullTime = {cullTime:,}
	drawTime = {drawTime:,}
	swapTime = {swapTime:,}
	gpuTime = {gpuTime:,}
	effectComposeTime = {effectComposeTime:,}
	primitiveCount = {primitiveCount:,}
	drawableCount = {drawableCount:,}
	systemMemory = {systemMemory:,}
	gpuMemory = {gpuMemory:,}
)""".format(**self.__dict__)

class NodeStats(object):
	def __init__(self,vertexCount,primitiveCount,drawableCount,textureCount,textureBytes,nodeCount,transformCount):
		self.vertexCount = vertexCount
		self.primitiveCount = primitiveCount
		self.drawableCount = drawableCount
		self.textureCount = textureCount
		self.textureBytes = textureBytes
		self.nodeCount = nodeCount
		self.transformCount = transformCount

	def __repr__(self):
		return """NodeStats(
	vertexCount = {vertexCount:,}
	primitiveCount = {primitiveCount:,}
	drawableCount = {drawableCount:,}
	transformCount = {transformCount:,}
	nodeCount = {nodeCount:,}
	textureCount = {textureCount:,}
	textureBytes = {textureBytes:,}
)""".format(**self.__dict__)

class StencilFunc(object):
	def __init__(self):
		self.func = GL_ALWAYS
		self.funcRef = 0
		self.funcMask = 0xffffffff # ~0u
		self.sfail = GL_KEEP
		self.zfail = GL_KEEP
		self.zpass = GL_KEEP
		self.writeMask = 0xffffffff # ~0u

	@staticmethod
	def RenderMask(mask=1):
		s = StencilFunc()
		s.func = GL_ALWAYS
		s.funcRef = mask
		s.writeMask = mask
		s.zpass = GL_REPLACE
		return s

	@staticmethod
	def RenderInsideMask(mask=1):
		s = StencilFunc()
		s.func = GL_EQUAL
		s.funcRef = mask
		s.funcMask = mask
		return s

	@staticmethod
	def RenderOutsideMask(mask=1):
		s = StencilFunc()
		s.func = GL_EQUAL
		s.funcRef = 0
		s.funcMask = mask
		return s

class TextureCombine(object):
	def __init__(self):
		self.combine_rgb = GL_MODULATE
		self.combine_alpha = GL_MODULATE
		self.source0_rgb = GL_TEXTURE
		self.source1_rgb = GL_PREVIOUS
		self.source2_rgb = GL_CONSTANT
		self.source0_alpha = GL_TEXTURE
		self.source1_alpha = GL_PREVIOUS
		self.source2_alpha = GL_CONSTANT
		self.operand0_rgb = GL_SRC_COLOR
		self.operand1_rgb = GL_SRC_COLOR
		self.operand2_rgb = GL_SRC_ALPHA
		self.operand0_alpha = GL_SRC_ALPHA
		self.operand1_alpha = GL_SRC_ALPHA
		self.operand2_alpha = GL_SRC_ALPHA
		self.scale_rgb = 1.0
		self.scale_alpha = 1.0
		self.constant_color = [ 0.0 , 0.0 , 0.0 , 0.0 ]

	#Shortcut functions
	def blend(self,value):
		self.combine_rgb = GL_INTERPOLATE
		self.source0_rgb = GL_TEXTURE
		self.source1_rgb = GL_PREVIOUS
		self.source2_rgb = GL_CONSTANT
		self.operand0_rgb = GL_SRC_COLOR
		self.operand1_rgb = GL_SRC_COLOR
		self.constant_color = [ value , value , value , value ]

class TextureGen(object):
	def __init__(self,mode=None,matrix=None):
		if mode is None:
			mode = GL_OBJECT_LINEAR
		if matrix is None:
			matrix = Matrix()
		self.mode = mode
		self.matrix = matrix

	def projectView(self,view,proj):
		"""Setup texgen to project using specified projection/view matrix"""

		#Use matrix projection mode
		self.mode = TEXGEN_PROJECT_MAT

		#Convert to OSG reference frame
		v = Matrix(view)
		v[2] = -v[2];
		v[6] = -v[6];
		v[8] = -v[8];
		v[9] = -v[9];
		v[14] = -v[14];
		v.invert()

		#Compute matrix
		self.matrix = v * proj * Matrix.translate(1,1,1) * Matrix.scale(0.5,0.5,0.5)

class RadioGroup(object):
	"""Radio button group"""

	def __init__(self,name):
		self.__name = name

	def getName(self):
		"""Get name of radio group"""
		return self.__name

	def getSelected(self):
		"""Get selected button in group"""
		return getSelectedRadio(self.__name)

	def getButtons(self):
		"""Return a list of buttons in the group"""
		return getRadioButtons(self.__name)

	def addButton(self,*args,**kw):
		"""Add a button to the group"""
		return addRadioButton(self.__name,*args,**kw)

class Theme(object):

	_COLORS = {  'borderColor'				: (0,None)
				,'textColor'				: (1,None)
				,'backColor'				: (2,None)
				,'darkBackColor'			: (3,'backColor')
				,'lightBackColor'			: (4,'backColor')
				,'highBackColor'			: (5,'backColor')
				,'highTextColor'			: (6,'textColor')
				,'highBorderColor'			: (7,'borderColor')
				,'activeBackColor'			: (8,'backColor')
				,'activeTextColor'			: (9,'textColor')
				,'activeBorderColor'		: (10,'borderColor')
				,'inactiveBackColor'		: (11,'backColor')
				,'inactiveTextColor'		: (12,'textColor')
				,'inactiveBorderColor'		: (13,'borderColor')
				,'inactiveHighBackColor'	: (14,'highBackColor')
				,'inactiveHighTextColor'	: (15,'highTextColor')
				,'inactiveHighBorderColor'	: (16,'highBorderColor')
	}

	def __init__(self,colors=None):

		self._colors = [ [1,1,1,1]
						,[1,1,1,1]
						,[1,1,1,1]
						,[1,1,1,1]
						,[1,1,1,1]
						,[1,1,1,1]
						,[1,1,1,1]
						,[-1,-1,-1,-1]
						,[-1,-1,-1,-1]
						,[-1,-1,-1,-1]
						,[-1,-1,-1,-1]
						,[-1,-1,-1,-1]
						,[-1,-1,-1,-1]
						,[-1,-1,-1,-1]
						,[-1,-1,-1,-1]
						,[-1,-1,-1,-1]
						,[-1,-1,-1,-1]
		]

		if colors:
			if isinstance(colors, Theme):
				colors = colors._colors
			for i,c in enumerate(colors):
				self._colors[i] = c

		# Dummy code so autocomplete parser displays attributes
		if False:
			self.borderColor				= (1,1,1,1)
			self.textColor					= (1,1,1,1)
			self.backColor					= (1,1,1,1)
			self.darkBackColor				= (1,1,1,1)
			self.lightBackColor				= (1,1,1,1)
			self.highBackColor				= (1,1,1,1)
			self.highTextColor				= (1,1,1,1)
			self.highBorderColor			= (1,1,1,1)
			self.activeBackColor			= (1,1,1,1)
			self.activeTextColor			= (1,1,1,1)
			self.activeBorderColor			= (1,1,1,1)
			self.inactiveBackColor			= (1,1,1,1)
			self.inactiveTextColor			= (1,1,1,1)
			self.inactiveBorderColor		= (1,1,1,1)
			self.inactiveHighBackColor		= (1,1,1,1)
			self.inactiveHighTextColor		= (1,1,1,1)
			self.inactiveHighBorderColor	= (1,1,1,1)

	def __getattr__(self, name):
		try:
			id,fallback = self._COLORS[name]
		except KeyError:
			 raise AttributeError
		v = self._colors[id]
		if fallback is not None and v[0] < 0.0:
			return getattr(self,fallback)
		return v

	def __setattr__(self, name, value):
		try:
			id,fallback = self._COLORS[name]
		except KeyError:
			return object.__setattr__(self,name,value)
		if len(value) < 4:
			value = list(value) + [1,1,1,1]
		self._colors[id] = list(value[:4])

	def _apply(self,mode):
		for i,v in enumerate(self._colors):
			_ipcSend(_VIZ_SETTHEMECOLOR,i,mode,'',v[0],v[1],v[2],v[3])

class Intersect(object):
	"""Intersect object"""
	def __init__(self,valid,point,normal,node,name,node_path,name_path):
		"""@arg node VizNode()
		@arg name ''
		"""
		self.valid = valid
		self.point = point
		self.normal = normal
		self.object = node
		self.object_path = node_path
		self.name = name
		self.name_path = name_path

	def __bool__(self):
		return self.valid

class Event(object):
	def __init__(self,**kw):
		self.__dict__.update(kw)
	def __repr__(self):
		combined = ', '.join((f'{name}={repr(value)}' for name, value in self.__dict__.items()))
		return f'viz.Event({combined})'

class Data(object):
	def __init__(self,**kw):
		self.__dict__.update(kw)
	def __repr__(self):
		combined = ', '.join((f'{name}={repr(value)}' for name, value in self.__dict__.items()))
		return f'viz.Data({combined})'

class CameraHandler(object): pass

Line = vizmat.Line
Plane = vizmat.Plane
BoundingBox = vizmat.BoundingBox
BoundingSphere = vizmat.BoundingSphere
Vector = vizmat.Vector
Quat = vizmat.Quat
Transform = vizmat.Transform
Matrix = vizmat.Transform

################################################################################################
################################################################################################
#									Constant Declarations									   #
################################################################################################
################################################################################################

#Viz Commands
_VIZ_ADDCHILD		= 0
_VIZ_STARTTIMER		= 1
_VIZ_TRANSLATECHILD	= 2
_VIZ_ROTATECHILD	= 3
_VIZ_SCALECHILD		= 4
_VIZ_CENTERCHILD	= 5
_VIZ_SHOWCHILD		= 6
_VIZ_COPYCHILD		= 7
_VIZ_CLONECHILD		= 8
_VIZ_SOUNDCHILD		= 9
_VIZ_PLAYSOUND		= 10
_VIZ_CHILDCOLOR		= 11
_VIZ_CHILDALPHA		= 12
_VIZ_CLEARCOLOR		= 13
_VIZ_GETCHILD		= 14
_VIZ_WINDOWPICK		= 15
_VIZ_TEXTVALUE		= 16
_VIZ_TEXTALIGN		= 17
_VIZ_TEXTURE		= 18
_VIZ_COMMANDMOD		= 19
_VIZ_ADDTEXTURE		= 20
_VIZ_ADDVIDEOTEX	= 21
_VIZ_ADDTEXT		= 22
_VIZ_ADDAUDIO		= 23
_VIZ_ADDLIGHT		= 24
_VIZ_ADDMAIL		= 25
_VIZ_ADDAVATAR		= 26
_VIZ_ADDSENSOR		= 27
_VIZ_ADDRENDERER	= 28
_VIZ_ADDSCENE		= 29
_VIZ_ADDVIEW		= 30
_VIZ_ADDWINDOW		= 31
_VIZ_TEXTFONT		= 32
_VIZ_TEXTRES		= 33
_VIZ_STARTLAYER		= 34
_VIZ_ENDLAYER		= 35
_VIZ_VERTEX			= 36
_VIZ_VERTEXCOLOR	= 37
_VIZ_LINEWIDTH		= 38
_VIZ_POINTSIZE		= 39
_VIZ_LIGHTPOS		= 40
_VIZ_LIGHTDIR		= 41
_VIZ_NODESTENCIL	= 42
_VIZ_ADDRENDERNODE	= 43
_VIZ_RENDERNODESET	= 44
_VIZ_LIGHTEXP		= 45
_VIZ_LIGHTCUTOFF	= 46
_VIZ_LIGHTCONSTANT	= 47
_VIZ_LIGHTLINEAR	= 48
_VIZ_LIGHTQUAD		= 49
_VIZ_LIGHTSHOW		= 50
_VIZ_MEDIAPLAY		= 51
_VIZ_MEDIASTOP		= 52
_VIZ_MEDIAPAUSE		= 53
_VIZ_MEDIAVOLUME	= 54
_VIZ_MEDIAPOS		= 55
_VIZ_MEDIARATE		= 56
_VIZ_MEDIALOOP		= 57
_VIZ_MEDIASTOPTIME	= 58
_VIZ_MEDIAGET		= 59
_VIZ_RESOURCESET	= 60
_VIZ_SENDMAIL		= 61
_VIZ_KILLTIMER		= 62
_VIZ_QUIT			= 63
_VIZ_CLIP			= 64
_VIZ_FOV			= 65
_VIZ_IPD			= 66
_VIZ_RENDERNODEGET	= 67
_VIZ_ISKEYDOWN		= 68
_VIZ_MOUSESET		= 69
_VIZ_MOUSEGET		= 70
_VIZ_RENDERTOWINDOW	= 71
_VIZ_NAVIGATEMOUSE	= 72
_VIZ_SETNODEMODE	= 73
_VIZ_TEXTSET		= 74
_VIZ_TEXTGET		= 75
_VIZ_PICKRECT		= 76
_VIZ_RUNCOMMAND		= 77
_VIZ_RESET			= 78
_VIZ_GET			= 79
_VIZ_EYEHEIGHT		= 81
_VIZ_AVATARLOD		= 82
_VIZ_AVATARSPEED	= 83
_VIZ_AVATAREXECUTE	= 84
_VIZ_AVATARBLEND	= 85
_VIZ_AVATARSTATE	= 86
_VIZ_LOGMESSAGE		= 87
_VIZ_RESETPLUGIN	= 88
_VIZ_COMMANDPLUGIN	= 89
_VIZ_GETPLUGIN		= 90
_VIZ_GETNODETEXTURE	= 91
_VIZ_PATHSET		= 93
_VIZ_PATHGET		= 94
_VIZ_UNLINKFACE		= 95
_VIZ_ROTCHILDEULER	= 96
_VIZ_OTFADDVERTEX	= 97
_VIZ_LOGSET			= 98
_VIZ_CHILDGET		= 99
_VIZ_SETSCENEMODE	= 100
_VIZ_SETAPPEARANCE	= 101
_VIZ_SETMATRIX1		= 102
_VIZ_SETMATRIX2		= 103
_VIZ_SETMATRIX3		= 104
_VIZ_SETMATRIX4		= 105
_VIZ_ADDCHECKBOX	= 106
_VIZ_UNCHECKPIC		= 107
_VIZ_CHECKPIC		= 108
_VIZ_GETCHECK		= 109
_VIZ_SETCHECK		= 110
_VIZ_PROGRESSSET	= 111
_VIZ_PROGRESSGET	= 112
_VIZ_ADDBUTTONLABEL	= 113
_VIZ_ADDSLIDER		= 114
_VIZ_SETTICKPOS		= 115
_VIZ_SETTICKSIZE	= 116
_VIZ_GETTICKPOS		= 117
_VIZ_SLIDERTICKPIC	= 118
_VIZ_SLIDERBACKPIC	= 119
_VIZ_NODECLIPPLANE	= 120
_VIZ_SLIDERMARGIN	= 121
_VIZ_SETGRAVITY		= 122
_VIZ_SETSTEPSIZE	= 123
_VIZ_COLLIDEBUFFER	= 124
_VIZ_ENABLECOLLIDE	= 125
_VIZ_MOVE			= 126
_VIZ_SETFUSEDIST	= 127
_VIZ_ISCHILDCULLED	= 128
_VIZ_PERFORMSOUND3D	= 129
_VIZ_SETLINEBEGIN	= 130
_VIZ_NODEINTERSECT	= 131
_VIZ_GETMODIFIER	= 132
_VIZ_TRANSVIEW		= 133
_VIZ_PATHREMOVE		= 134
_VIZ_ROTAXISVIEW	= 135
_VIZ_ROTEULERVIEW	= 136
_VIZ_SETVELOCITY	= 137
_VIZ_GETVELOCITY	= 138
_VIZ_MOVERELATIVE	= 139
_VIZ_COLLIDECOPY	= 140
_VIZ_COLLIDEFILE	= 141
_VIZ_VIEWLOOKAT		= 142
_VIZ_NODESETTAG		= 143
_VIZ_SETTAGRENDER	= 144
_VIZ_REMOVECHILD	= 145
_VIZ_GO				= 146
_VIZ_SETSCENE		= 147
_VIZ_ADDTEXQUAD		= 148
_VIZ_NODEGRABTEX	= 149
_VIZ_AVATARCLEAR	= 150
_VIZ_SPLASHSCREEN	= 151
_VIZ_SLIDERDRAGGING	= 152
_VIZ_SETVIEWMATRIX	= 153
_VIZ_SETCHILDMATRIX	= 154
_VIZ_SAVECHILD		= 155
_VIZ_LIGHTINTENSITY	= 156
_VIZ_ROTQUATVIEW	= 157
_VIZ_MODIFYTEXTURE	= 158
_VIZ_MODIFYPARAMS	= 159
_VIZ_RESETMATRIX	= 160
_VIZ_ADDMODIFIER	= 161
_VIZ_MODIFY			= 162
_VIZ_ADDIMAGEGEN	= 163
_VIZ_COMMANDIMGGEN	= 164
_VIZ_INITPLUGIN		= 165
_VIZ_ADDGROUP		= 166
_VIZ_BILLBOARDNODE	= 167
_VIZ_ADDCUSTOM1		= 168
_VIZ_ADDCUSTOM2		= 169
_VIZ_COMMANDCUSTOM	= 170
_VIZ_GETCUSTOMDATA	= 171
_VIZ_WINDOWORDER	= 172
_VIZ_LOADTEXTURE	= 173
_VIZ_STATSSET		= 174
_VIZ_WINDOWVISIBLE	= 175
_VIZ_GETIMAGEGEN	= 176
_VIZ_PICKDETAIL		= 177
_VIZ_EXTCOMMAND		= 178
_VIZ_ADDEXTNODE		= 179
_VIZ_CMDEXTNODE		= 180
_VIZ_ADDEXTTEX		= 181
_VIZ_CMDEXTTEX		= 182
_VIZ_EXTMODNODE		= 183
_VIZ_EXTMODTEX		= 184
_VIZ_ADDSHADER		= 185
_VIZ_SHADERSET		= 186
_VIZ_ADDUNIFORM		= 187
_VIZ_SETUNIFORM		= 188
_VIZ_APPLYSHADER	= 189
_VIZ_APPLYUNIFORM	= 190
_VIZ_TEXWRAPMODE	= 191
_VIZ_TEXFILTERMODE	= 192
_VIZ_SCREENDIST		= 193
_VIZ_ROTQUATCHILD	= 194
_VIZ_HINTSCENE		= 195
_VIZ_NEARFARRATIO	= 196
_VIZ_SETFONTSIZE	= 197
_VIZ_UPDATEFRAME	= 198
_VIZ_AVATARRATE		= 199
_VIZ_SETFOGMODE		= 200
_VIZ_SETFOGCOLOR	= 201
_VIZ_NORMAL			= 202
_VIZ_OTFNORMAL		= 203
_VIZ_EXTGET			= 204
_VIZ_ADDEXTSENSOR	= 205
_VIZ_CMDEXTSENSOR	= 206
_VIZ_RSTEXTSENSOR	= 207
_VIZ_GETEXTSENSOR	= 208
_VIZ_LINKSETOP		= 209
_VIZ_WAITTIME		= 210
_VIZ_WINDOWSIZE		= 211
_VIZ_WINDOWPOS		= 212
_VIZ_WINDOWVIEW		= 213
_VIZ_WINDOWCOORDS	= 214
_VIZ_COLLIDEPLANE	= 215
_VIZ_COLLIDECAP		= 216
_VIZ_SCREENTOWORLD	= 217
_VIZ_UNIFORMREMOVE	= 218
_VIZ_COLLIDENONE	= 219
_VIZ_APPLYFORCE		= 220
_VIZ_SETSTRING		= 221
_VIZ_APPLYTORQUE	= 222
_VIZ_ANGULARVEL		= 223
_VIZ_CHILDLOOKAT	= 224
_VIZ_WAITFORKEY		= 225
_VIZ_NODECMDPHYS	= 226
_VIZ_COLLIDECUSTOM	= 227
_VIZ_ROTEULERBONE	= 228
_VIZ_GETAVATARBONE	= 229
_VIZ_LOCKBONE		= 230
_VIZ_ROTAXISBONE	= 231
_VIZ_ROTQUATBONE	= 232
_VIZ_TRANSLATEBONE	= 233
_VIZ_NETWORKGET		= 234
_VIZ_TEXCOORD		= 235
_VIZ_APPLYFORCEPOS	= 236
_VIZ_SETPHYSPOS		= 237
_VIZ_SETPHYSROT		= 238
_VIZ_STATSCHILD		= 239
_VIZ_PHYSGRAVITY	= 240
_VIZ_SCENEVISIBLE	= 241
_VIZ_GUIENABLE		= 242
_VIZ_ADDANIMPATH	= 243
_VIZ_ADDCTRLPOINT	= 244
_VIZ_PATHADDPOINT	= 245
_VIZ_PATHLOOPMODE	= 246
_VIZ_PATHAUTOROT	= 247
_VIZ_PATHINTERPMODE	= 248
_VIZ_PATHSPEED		= 249
_VIZ_PATHPAUSE		= 250
_VIZ_PATHCOMPUTETAN	= 251
_VIZ_POINTDATA		= 252
_VIZ_POINTDATAIN	= 253
_VIZ_POINTDATAOUT	= 254
_VIZ_POINTINTERP	= 255
_VIZ_SETANIMATION	= 256
_VIZ_GETANIMATION	= 257
_VIZ_SCENESTATS		= 258
_VIZ_ADDRADIOBUTTON	= 259
_VIZ_OFFSETBONE		= 260
_VIZ_SETBONEMAT		= 261
_VIZ_GETBONEINFO	= 262
_VIZ_PATHCONSTVEL	= 263
_VIZ_STEREOOVERLAP	= 264
_VIZ_NODESETUNIFORM	= 265
_VIZ_PAUSETIMERS	= 266
_VIZ_TIMERELAPSED	= 267
_VIZ_DRAWORDER		= 268
_VIZ_ADDFACE		= 269
_VIZ_COLLIDEBOX		= 270
_VIZ_COLLIDESPHERE	= 271
_VIZ_COLLIDEMESH	= 272
_VIZ_COLLIDINGCHILD	= 273
_VIZ_FACEMORPH		= 274
_VIZ_OPTIMIZECHILD	= 275
_VIZ_NODEPOLY		= 276
_VIZ_LINKFACEAVATAR = 277
_VIZ_MODIFYSCENE	= 278
_VIZ_WORLDTOSCREEN	= 279
_VIZ_PHYSICSGET		= 280
_VIZ_TEXTENCODING	= 281
_VIZ_EFFECTSETMAT	= 286
_VIZ_EFFECTSETPROP	= 287
_VIZ_PHYSMATERIAL	= 288
_VIZ_PATHRESET		= 289
_VIZ_CLEARMORPH		= 290
_VIZ_SETPARENT		= 291
_VIZ_EFFECTSET		= 292
_VIZ_ADDRESCONTEXT	= 293
_VIZ_VIEWOFFSET		= 294
_VIZ_CPREMOVE		= 295
_VIZ_ADDRENDERTEX	= 296
_VIZ_VIEWGET		= 297
_VIZ_AVATARSETTIME	= 298
_VIZ_CLIENTCALLBACK	= 299
_VIZ_PHYSADDJOINT	= 300
_VIZ_CLUSTERGET		= 301
_VIZ_TEXBLEND		= 302
_VIZ_SETOPTION		= 303
_VIZ_OTFVERTEX		= 304
_VIZ_OTFCOLOR		= 305
_VIZ_OTFTEXCOORD	= 306
_VIZ_STEREOMODE		= 307
_VIZ_CREATELINKABLE	= 308
_VIZ_DUPLICATECHILD	= 309
_VIZ_SETTEXMAT		= 310
_VIZ_WINSETFRUSTUM	= 311
_VIZ_NODETEXGEN		= 312
_VIZ_SETVSYNC		= 313
_VIZ_REGISTERCLASS	= 314
_VIZ_ADDTEXTBOX		= 315
_VIZ_ADDPROGRESSBAR	= 316
_VIZ_COMMANDSOUND3D = 317
_VIZ_SOUND3DENGINE	= 318
_VIZ_ADDDROPLIST	= 319
_VIZ_NODEVELOCITY	= 320
_VIZ_OVERFLOWMODE	= 321
_VIZ_NETWORKSET		= 322
_VIZ_LISTENPORT		= 323
_VIZ_GUISETLENGTH	= 324
_VIZ_QUEUECOMMAND	= 325
_VIZ_ADDNETWORK		= 327
_VIZ_SENDNETWORK	= 328
_VIZ_GETEVENTID		= 329
_VIZ_DIRECTORMODE	= 330
_VIZ_SCENEGET		= 331
_VIZ_WINDOWGET		= 332
_VIZ_DISPLAYSET		= 333
_VIZ_DISPLAYGET		= 334
_VIZ_BONELOOK		= 335
_VIZ_TEXREMOVE		= 336
_VIZ_TEXCOMPRESS	= 337
_VIZ_TEXTUREGET		= 338
_VIZ_CLEARCACHE		= 339
_VIZ_ADDEXTENSION	= 341
_VIZ_TEXANISOTROPY	= 342
_VIZ_FOCUSNODE		= 343
_VIZ_SETCURSORPOS	= 344
_VIZ_DELNETWORK		= 345
_VIZ_DELMEDIA		= 346
_VIZ_DROPLISTMODIFY	= 347
_VIZ_SETTHEMECOLOR	= 348
_VIZ_LINKSET		= 349
_VIZ_LINKGET		= 350
_VIZ_LINKCREATE		= 351
_VIZ_LINKABLE_GET	= 352
_VIZ_SCENEINTERSECT	= 353
_VIZ_NODEGLFUNC		= 354
_VIZ_JOINTSET		= 355
_VIZ_JOINTCOMMAND	= 356
_VIZ_JOINTGET		= 357
_VIZ_RESETCAMERA	= 358
_VIZ_AVATARMORPH	= 359
_VIZ_ADDEFFECT		= 360
_VIZ_TEXTURESET		= 361
_VIZ_MEDIABALANCE	= 362
_VIZ_WINDOWREMOVE	= 363
_VIZ_VIEWREMOVE		= 364
_VIZ_SCENEREMOVE	= 365
_VIZ_TEXBORDERCOLOR	= 366
_VIZ_SETNODEMASK	= 367
_VIZ_UNIFORMGET		= 368
_VIZ_SOUND3DGET		= 369
_VIZ_WINDOWSET		= 370
_VIZ_LINKABLESET	= 371
_VIZ_SOUND3DREMOVE	= 372
_VIZ_ADDEXTOBJECT	= 373
_VIZ_CMDEXTOBJECT	= 374
_VIZ_DELEXTOBJECT	= 375
_VIZ_SETEVTHANDLER	= 376
_VIZ_ADDGUIGROUP	= 377
_VIZ_DELEXTSENSOR	= 378
_VIZ_GUISETMODAL	= 379
_VIZ_MEDIASET		= 380
_VIZ_ADDBLANKTEX	= 381
_VIZ_EXTMODLINKABLE = 382
_VIZ_ADDTEXBUFFER	= 383
_VIZ_ADDCHILDBUFFER	= 384
_VIZ_NODEANISOTROPY	= 385
_VIZ_SETOPMODE		= 386
_VIZ_CLEARATTRIBUTE	= 387
_VIZ_EFFECTGET		= 388
_VIZ_TEXSETDATA		= 389
_VIZ_RESCONTEXTSET	= 390
_VIZ_RESCONTEXTGET	= 391
_VIZ_WINDOWCULLMASK	= 392
_VIZ_QUEUEPHYSCMD	= 393
_VIZ_LIGHTSET		= 394
_VIZ_LIGHTGET		= 395
_VIZ_MIXERSET		= 396
_VIZ_MIXERGET		= 397
_VIZ_NODEBOXSET		= 398
_VIZ_GUICANVASSET	= 399
_VIZ_GUICANVASGET	= 400
_VIZ_NODETEXSET		= 401
_VIZ_USERSET		= 402
_VIZ_USERGET		= 403
_VIZ_GETSENSORCHILD	= 404
_VIZ_CMDPARTICLE	= 405
_VIZ_SETMATERIAL	= 406
_VIZ_SETCOMPALPHA	= 407

# Delimeter for name list strings
_NAME_DELIMETER = '\x1f'

# Event action flags
EVENT_STOP				= 0x1
EVENT_PREVENT_DEFAULT	= 0x2

#Priority for input tasks
PRIORITY_GUI_HANDLER		= -20
PRIORITY_CAMERA_HANDLER		= -10
PRIORITY_DEFAULT_KEY		= -5

#Priority for update tasks
PRIORITY_FIRST_UPDATE		= -50
PRIORITY_PLUGINS			= -50
PRIORITY_INPUT				= -40
PRIORITY_NETWORK			= -30
PRIORITY_SCENEGRAPH			= -20
PRIORITY_TIMERS				= -10
PRIORITY_DEFAULT			= 0
PRIORITY_HOTSPOT			= DeprecateObject(10)
PRIORITY_PHYSICS			= 20
PRIORITY_LINKS				= 40
PRIORITY_MEDIA				= 50
PRIORITY_LAST_UPDATE		= 50

#Manual update flags
UPDATE_PLUGINS			= 1
UPDATE_INPUT			= 2
UPDATE_NETWORK			= 4
UPDATE_SCENEGRAPH		= 8
UPDATE_TIMERS			= 16
UPDATE_HOTSPOT			= DeprecateObject(32)
UPDATE_PHYSICS			= 64
UPDATE_LINKS			= 128
UPDATE_MEDIA			= 256
UPDATE_POSTED_EVENTS	= 512

#Built-in events
KEYDOWN_EVENT				= 0
KEYUP_EVENT					= 1
MOUSEDOWN_EVENT				= 2
MOUSEUP_EVENT				= 3
MOUSEWHEEL_EVENT			= 4
PATH_EVENT					= 5
EXIT_EVENT					= 6
TIMER_EVENT					= 7
MAIL_EVENT					= 8
BUTTON_EVENT				= 9
SLIDER_EVENT				= 10
COLLISION_EVENT				= 12
UPDATE_EVENT				= 13
NETWORK_EVENT				= 14
TEXTBOX_EVENT				= 15
LIST_EVENT					= 16
WINDOW_SIZE_EVENT			= 17
ANIMATION_END_EVENT			= 18
PRE_SWAP_EVENT				= 19
POST_SWAP_EVENT				= 20
INIT_EVENT					= 21
COLLIDE_BEGIN_EVENT			= 22
MOUSE_MOVE_EVENT			= 23
COLLIDE_END_EVENT			= 24
JOINT_BREAK_EVENT			= 25
MEDIA_EVENT					= 26
SENSOR_DOWN_EVENT			= 27
SENSOR_UP_EVENT				= 28
OPTION_EVENT				= 29
DOUBLE_CLICK_EVENT			= 30
KEY_CHAR_EVENT				= 32
WINDOW_EVENT				= 33
ANIMATION_DELAY_OUT_EVENT	= 34
ASYNC_EVENT					= 35
HOVER_EVENT					= 37
MONITOR_CHANGE_EVENT		= 39

#External Viz Events (values must be below 200)
ACTION_END_EVENT	= 100
ACTION_BEGIN_EVENT	= 101
ACTION_EMPTY_EVENT	= 102
SENSOR_RECORD_EVENT	= 103

def _triggerSensorRecordEvent(sensorID,data):
	"""FOR INTERNAL USE ONLY"""
	sendEvent(SENSOR_RECORD_EVENT,Event(object=VizExtensionSensor._GetObject(sensorID),data=data))

FRAME_EVENT			= DeprecateObject(UPDATE_EVENT)
STOP_EVENT			= DeprecateObject(ACTION_END_EVENT)
AVATAR_END_EVENT	= DeprecateObject(ACTION_END_EVENT)
AVATAR_BEGIN_EVENT	= DeprecateObject(ACTION_BEGIN_EVENT)
AVATAR_IDLE_EVENT	= DeprecateObject(ACTION_EMPTY_EVENT)

#Log modes
LOG_ALWAYS					= 0
LOG_ERROR					= 1
LOG_WARN					= 2
LOG_NOTICE					= 3
LOG_INFO					= 4
LOG_DEBUG					= 6
LOG_STATUS					= -1
LOG_SPLASH					= -2
LOG_SPLASH_BEGIN_GROUP		= -3
LOG_SPLASH_END_GROUP		= -4
LOG_SPLASH_BEGIN_OVERRIDE	= -5
LOG_SPLASH_END_OVERRIDE		= -6

#Screen capture flags
CAPTURE_RGBA			= 1
CAPTURE_COPY_TEXTURE	= 2

#Node mask modes
MASK_SET		= 0
MASK_ADD		= 1
MASK_REMOVE		= 2
MASK_TOGGLE		= 3

# Tag existence check modes
TAG_HAS_ALL				= 0x1
TAG_HAS_ANY				= 0x2

# Tag render modes
TAG_RENDER_DEFAULT		= 0x1
TAG_RENDER_ENABLED		= 0x2
TAG_RENDER_DISABLED		= 0x4

#Draw order bin modes
BIN_OPAQUE			= 0
BIN_TRANSPARENT		= 1
BIN_BACK_TO_FRONT	= 2
BIN_FRONT_TO_BACK	= 3
BIN_TRAVERSAL_ORDER	= 4

#Reserved node masks
PICK_MASK			= 1
INTERSECT_MASK		= 2
GUI_MASK			= 4
LEFT_MASK			= 8
RIGHT_MASK			= 16
MASK_SHADOW_CAST	= 32
LAST_MASK			= 32

ALL_MASK_BITS	= 0xffffffff

def addNodeMask():
	"""Returns a unique node mask"""
	global LAST_MASK
	if (LAST_MASK << 1) > ALL_MASK_BITS:
		raise OverflowError('Number of allowable node masks has been exceeded')
	LAST_MASK = LAST_MASK << 1
	return LAST_MASK

LAST_WINDOW_MESSAGE = 0x8000 # WM_APP

def createWindowMessage():
	"""Create and returns a new custom Windows message ID for use within this process"""
	global LAST_WINDOW_MESSAGE
	id = LAST_WINDOW_MESSAGE
	LAST_WINDOW_MESSAGE += 1
	return id

#Rotation mode load flags
ROTATE_DEFAULT	= 0
ROTATE_NONE		= 1
ROTATE_Y_UP		= 1
ROTATE_Z_UP		= 2

#Cache mode load flags
CACHE_DEFAULT	= 0
CACHE_NONE		= 4
CACHE_COPY		= 8
CACHE_CLONE		= 16

#Load flags
LOAD_ASYNC					= 0x20
LOAD_IGNORE_LIGHTS			= 0x4000
LOAD_IGNORE_SCENE_SETTINGS	= 0x8000

#Avatar load flags
AVATAR_DELAY_LOAD	= 64

#Effect generate flags
EFFECTGEN_OSGMAXEXP			= 512
EFFECTGEN_CAL3D				= 1024
EFFECTGEN_ATTR_TEXTURE		= 2048
EFFECTGEN_ATTR_COLOR		= 4096
EFFECTGEN_ATTR_ALL			= EFFECTGEN_ATTR_TEXTURE | EFFECTGEN_ATTR_COLOR
EFFECTGEN_DEFAULT			= EFFECTGEN_OSGMAXEXP | EFFECTGEN_CAL3D | EFFECTGEN_ATTR_ALL

# Get child flags
CHILD_INSERT_TRANSFORM		= 0
CHILD_REPLACE_TRANSFORM		= 1
CHILD_DEFAULT			 	= CHILD_INSERT_TRANSFORM

# Node type flags
TYPE_NODE					= 0x1
TYPE_GROUP					= 0x2
TYPE_TRANSFORM				= 0x4
TYPE_GEODE					= 0x8
TYPE_DRAWABLE				= 0x10
TYPE_LIGHT					= 0x20
TYPE_SWITCH					= 0x40
TYPE_AVATAR					= 0x80
TYPE_PARTICLE				= 0x100
TYPE_TEXT					= 0x200
TYPE_BACKGROUND				= 0x400
TYPE_SEQUENCE				= 0x800
TYPE_OCCLUDER				= 0x1000
TYPE_LOD					= 0x2000
TYPE_CHILDREN				= 0x1000000
TYPE_PARENTS				= 0x2000000
TYPE_ALL					= 0xffffff & ~(TYPE_CHILDREN | TYPE_PARENTS)

# Async status modes
ASYNC_STOPPED	= 0
ASYNC_LOADING	= 1
ASYNC_SUCCESS	= 2
ASYNC_FAIL		= 3

#Render order modes
PRE_RENDER		= 0
POST_RENDER		= 1
MAIN_RENDER		= 2

#Render buffer modes
RENDER_FBO				= 1
RENDER_FRAME_BUFFER		= 2

#Render texture buffers
RENDER_DEPTH			= 0
RENDER_STENCIL			= 1
RENDER_DEPTH_STENCIL	= 2
RENDER_COLOR			= 3
RENDER_COLOR0			= 4

#Render texture formats
TEX_RGB				= 0
TEX_RGBA			= 1
TEX_RGB_16			= 2
TEX_RGBA_16			= 3
TEX_RGB_32			= 4
TEX_RGBA_32			= 5
TEX_DEPTH			= 6
TEX_DEPTH_16		= 7
TEX_DEPTH_24		= 8
TEX_DEPTH_32		= 9
TEX_LUMINANCE		= 10
TEX_ALPHA			= 11
TEX_LUMINANCE_ALPHA	= 12
TEX_BGR				= 13
TEX_BGRA			= 14
TEX_DEPTH_STENCIL	= 15

# Canvas child names
CANVAS_CURSOR		= "canvas_cursor"

# Canvas render modes
CANVAS_WORLD_OVERLAY			= 0
CANVAS_WORLD					= 1
CANVAS_SCREEN_ORTHO				= 2
CANVAS_SCREEN_PERSPECTIVE		= 3

# Canvas mouse style flags
CANVAS_MOUSE_BUTTON				= 0x1
CANVAS_MOUSE_MOVE				= 0x2
CANVAS_MOUSE_POSITION			= 0x4
CANVAS_MOUSE_VISIBLE			= 0x8
CANVAS_MOUSE_VIRTUAL			= (CANVAS_MOUSE_BUTTON | CANVAS_MOUSE_MOVE | CANVAS_MOUSE_VISIBLE)
CANVAS_MOUSE_REAL				= (CANVAS_MOUSE_BUTTON | CANVAS_MOUSE_POSITION)

#Clip plane modes
CLIP_GLOBAL		= 0
CLIP_LOCAL		= 1
CLIP_VIEW		= 2
CLIP_EYE		= 3

#Mouse visible modes
MOUSE_AUTO_HIDE	= 2

#Border modes
BORDER_NONE		= 0
BORDER_RESIZE	= 1
BORDER_FIXED	= 2

#Frame rate modes
FRAMERATE_NONE		= 0
FRAMERATE_SIMPLE	= 1
FRAMERATE_DETAILS	= 2

#Director mode
DIRECTOR_FAST	= 0
DIRECTOR_SAFE	= 1

#Mouse button states
MOUSEBUTTON_LEFT		= 1
MOUSEBUTTON_MIDDLE		= 2
MOUSEBUTTON_RIGHT		= 4

#Mouse position modes
WINDOW_NORMALIZED	= 0
WINDOW_PIXELS		= 1
SCREEN_PIXELS		= 2
WINDOW_ORTHO		= 3
RELATIVE_PIXELS		= 4

#Text overflow modes
OVERFLOW_RESIZE			= 0x1
OVERFLOW_WRAP			= 0x2
OVERFLOW_CROP_HORZ		= 0x4
OVERFLOW_CROP_VERT		= 0x8
# Backwards compatibility
OVERFLOW_GROW		= 0
OVERFLOW_SHRINK		= OVERFLOW_RESIZE
OVERFLOW_CROP		= OVERFLOW_CROP_HORZ | OVERFLOW_CROP_VERT

#Text alignment values
ALIGN_LEFT_TOP				= TEXT_LEFT_TOP			= 0
ALIGN_LEFT_CENTER			= TEXT_LEFT_CENTER		= 1
ALIGN_LEFT_BOTTOM			= TEXT_LEFT_BOTTOM		= 2
ALIGN_CENTER_TOP			= TEXT_CENTER_TOP		= 3
ALIGN_CENTER_CENTER			= TEXT_CENTER_CENTER	= 4
ALIGN_CENTER_BOTTOM			= TEXT_CENTER_BOTTOM	= 5
ALIGN_RIGHT_TOP				= TEXT_RIGHT_TOP		= 6
ALIGN_RIGHT_CENTER			= TEXT_RIGHT_CENTER		= 7
ALIGN_RIGHT_BOTTOM			= TEXT_RIGHT_BOTTOM		= 8
ALIGN_LEFT_BASE				= TEXT_LEFT_BASE		= 9
ALIGN_CENTER_BASE			= TEXT_CENTER_BASE		= 10
ALIGN_RIGHT_BASE			= TEXT_RIGHT_BASE		= 11
ALIGN_LEFT_BOTTOM_BASE		= 12
ALIGN_CENTER_BOTTOM_BASE	= 13
ALIGN_RIGHT_BOTTOM_BASE		= 14
ALIGN_CENTER 		= ALIGN_CENTER_CENTER #For convenience

#Text backdrop modes
BACKDROP_NONE			= 0
BACKDROP_RIGHT_BOTTOM	= 1
BACKDROP_RIGHT_CENTER	= 2
BACKDROP_RIGHT_TOP		= 3
BACKDROP_CENTER_BOTTOM	= 4
BACKDROP_CENTER_TOP		= 5
BACKDROP_LEFT_BOTTOM	= 6
BACKDROP_LEFT_CENTER	= 7
BACKDROP_LEFT_TOP		= 8
BACKDROP_OUTLINE		= 9
BACKDROP_BOX			= 10

#Text font hints
FONT_HINT_NEAREST_FILTERING		= 1
FONT_HINT_BOLD					= 2
FONT_HINT_ITALIC				= 4
FONT_HINT_BOLD_ITALIC			= (FONT_HINT_BOLD | FONT_HINT_ITALIC)

#Billboard modes
BILLBOARD_VIEW			= 1
BILLBOARD_YAXIS_LOCAL	= 2
BILLBOARD_VIEW_POS		= 3
BILLBOARD_XYAXIS_LOCAL	= 4
BILLBOARD_YAXIS_GLOBAL	= 5
BILLBOARD_XYAXIS_GLOBAL	= 6
BILLBOARD_SCREEN_PIXELS	= 7
BILLBOARD_SCREEN_WORLD	= 8
BILLBOARD_YAXIS			= DeprecateObject(BILLBOARD_YAXIS_LOCAL)
BILLBOARD_XYAXIS		= DeprecateObject(BILLBOARD_XYAXIS_LOCAL)

#Box transform flags
BOX_DISABLED		= 0
BOX_ENABLED			= 0x1
BOX_FIXED			= 0x2
BOX_ROOT			= 0x4
BOX_PIXEL_PERFECT	= 0x8

#Node reference frame modes
RF_PARENT	= 0
RF_VIEW		= 1
RF_EYE		= 2
RF_GLOBAL	= 3
RF_VIEW_POS	= 4
RF_EYE_POS	= 5

#Texture compression modes
COMPRESSION_DEFAULT		= 0
COMPRESSION_ARB			= 2
COMPRESSION_DXT1		= 3
COMPRESSION_DXT3		= 4
COMPRESSION_DXT5		= 5

#Cache clearing flags
TEXTURE_CACHE	= 1
NODE_CACHE		= 2
SOUND_CACHE		= 4

#HTML options
HTML_TOGGLE		= 1
HTML_RESIZE		= 2
HTML_POSITION	= 4

#Cluster variables
ALLCLIENTS	= 0xffffffff
MASTER		= 1
CLIENT1		= 2
CLIENT2		= 4
CLIENT3		= 8
CLIENT4		= 16
CLIENT5		= 32
CLIENT6		= 64
CLIENT7		= 128
CLIENT8		= 256
CLIENT9		= 512

#User tracker names
USER_ORIGIN		= 'origin'
USER_HEAD		= 'head'
USER_HAND_LEFT	= 'hand_left'
USER_HAND_RIGHT	= 'hand_right'

#Modes for fusion distance
DISTANCE		= 0
PROPORTIONAL	= 1

#Interpolation modes for animation paths
INHERIT			= 0
LINEAR_INTERP	= 1
BEZIER			= 2
CUBIC_BEZIER	= 3

#Loop modes for animation paths (0 and 1 are OFF and LOOP, which are declared elsewhere)
SWING		= 2
CIRCULAR	= 3

#Viz Modes
CHECKERBOARD	= 0x00000001
INTERLACE_HORZ	= 0x00000002
STEREO_VERT     = 0x00000004
ANAGLYPHIC		= 0x00000008
PROMPT			= 0x00000010
FULLSCREEN		= 0x00000020
STEREO_HORZ		= 0x00000040
TRACKER			= 0x00000080
OPTION1			= 0x00000100
OPTION2			= 0x00000200
INITMESG		= 0x00000400
EMBEDDED		= 0x00000800
NO_DEFAULT_KEY	= 0x00001000
QUAD_BUFFER		= 0x00002000
STENCIL_BUFFER	= 0x00004000
INTERLACE_VERT	= 0x00008000
ACTKERN			= 0x00010000
STEREO_RIGHT	= 0x00020000
STEREO_LEFT		= 0x00040000
HMD				= 0x00080000
HALF_RESOLUTION	= 0x00100000

# Shortcuts for 3D TV stereo formats
STEREO_3DTV_SIDE_BY_SIDE	= STEREO_HORZ | HALF_RESOLUTION
STEREO_3DTV_TOP_AND_BOTTOM	= STEREO_VERT | HALF_RESOLUTION

#************************************************************
# GL ENABLE and DISABLE COMMANDS (taken from gl.h)
# These are the #defs with the #define  GL_ stripped off
ALPHA_TEST						= 0x0BC0
BLEND							= 0x0BE2
CW								= 0x0900
CCW								= 0x0901
COLOR_MATERIAL					= 0x0B57
CULL_FACE						= 0x0B44
DEPTH_TEST						= 0x0B71
FLAT							= 0x1D00
FOG								= 0x0B60
LIGHT0							= 0x4000
LIGHT1							= 0x4001
LIGHT2							= 0x4002
LIGHT3							= 0x4003
LIGHT4							= 0x4004
LIGHT5							= 0x4005
LIGHT6							= 0x4006
LIGHT7							= 0x4007
LIGHTING						= 0x0B50
LINES							= 0x0001
LINE_LOOP						= 0x0002
LINE_STRIP						= 0x0003
NORMALIZE						= 0x0BA1
POINTS							= 0x0000
POLYGON							= 0x0009
POLYGON_SMOOTH					= 0x0B41
POLYGON_STIPPLE					= 0x0B42
QUADS							= 0x0007
QUAD_STRIP						= 0x0008
SCISSOR_TEST					= 0x0C11
SMOOTH							= 0x1D01
STENCIL_TEST					= 0x0B90
TEXTURE_2D						= 0x0DE1
TRIANGLES						= 0x0004
TRIANGLE_FAN					= 0x0006
TRIANGLE_STRIP					= 0x0005
POINT_SMOOTH					= 0x0B10
LINE_SMOOTH						= 0x0B20
EXP								= 0x0800
EXP2							= 0x0801
LINEAR							= 0x2601
LINEAR_MIPMAP_LINEAR			= 0x2703
LINEAR_MIPMAP_NEAREST			= 0x2701
NEAREST							= 0x2600
NEAREST_MIPMAP_LINEAR			= 0x2702
NEAREST_MIPMAP_NEAREST			= 0x2700
CLAMP							= 0x2900
CLAMP_TO_EDGE					= 0x812F
CLAMP_TO_BORDER					= 0x812D
REPEAT							= 0x2901
MIRROR							= 0x8370
SAMPLE_ALPHA_TO_COVERAGE		= 0x809E
DEPTH_CLAMP						= 0x864F

#OpenGL face modes
GL_FRONT						= 0x0404
GL_BACK							= 0x0405
GL_FRONT_AND_BACK				= 0x0408

#Stencil function operation mode
GL_KEEP							= 0x1E00
GL_INCR							= 0x1E02
GL_DECR							= 0x1E03
GL_INVERT						= 0x150A
GL_INCR_WRAP					= 0x8507
GL_DECR_WRAP					= 0x8508

#Depth/Stencil function modes
GL_NEVER						= 0x0200
GL_LESS							= 0x0201
GL_EQUAL						= 0x0202
GL_LEQUAL						= 0x0203
GL_GREATER						= 0x0204
GL_NOTEQUAL						= 0x0205
GL_GEQUAL						= 0x0206
GL_ALWAYS						= 0x0207

#Blend function factors
GL_ZERO							= 0
GL_ONE							= 1
GL_SRC_COLOR					= 0x0300
GL_ONE_MINUS_SRC_COLOR			= 0x0301
GL_SRC_ALPHA					= 0x0302
GL_ONE_MINUS_SRC_ALPHA			= 0x0303
GL_DST_ALPHA					= 0x0304
GL_ONE_MINUS_DST_ALPHA			= 0x0305
GL_DST_COLOR					= 0x0306
GL_ONE_MINUS_DST_COLOR			= 0x0307
GL_SRC_ALPHA_SATURATE			= 0x0308
GL_CONSTANT_COLOR				= 0x8001
GL_ONE_MINUS_CONSTANT_COLOR		= 0x8002
GL_CONSTANT_ALPHA				= 0x8003
GL_ONE_MINUS_CONSTANT_ALPHA		= 0x8004

#TextureCombine combine modes
GL_REPLACE						= 0x1E01
GL_MODULATE						= 0x2100
GL_ADD							= 0x0104
GL_ADD_SIGNED					= 0x8574
GL_INTERPOLATE					= 0x8575
GL_SUBTRACT						= 0x84E7
GL_DOT3_RGB						= 0x86AE
GL_DOT3_RGBA					= 0x86AF

#TextureCombine source modes
GL_CONSTANT						= 0x8576
GL_PRIMARY_COLOR				= 0x8577
GL_PREVIOUS						= 0x8578
GL_TEXTURE						= 0x1702
GL_TEXTURE0						= 0x84C0
GL_TEXTURE1						= GL_TEXTURE0+1
GL_TEXTURE2						= GL_TEXTURE0+2
GL_TEXTURE3						= GL_TEXTURE0+3
GL_TEXTURE4						= GL_TEXTURE0+4
GL_TEXTURE5						= GL_TEXTURE0+5
GL_TEXTURE6						= GL_TEXTURE0+6
GL_TEXTURE7						= GL_TEXTURE0+7

#TextureGen modes
GL_OBJECT_LINEAR	= 0x2401
GL_EYE_LINEAR		= 0x2400
GL_SPHERE_MAP		= 0x2402
GL_NORMAL_MAP		= 0x8511
GL_REFLECTION_MAP	= 0x8512
TEXGEN_PROJECT_EYE	= -2
TEXGEN_PROJECT_MAT	= -3

#Clear masks
GL_DEPTH_BUFFER_BIT				= 0x00000100
GL_STENCIL_BUFFER_BIT			= 0x00000400
GL_COLOR_BUFFER_BIT				= 0x00004000

#OpenGL data types
GL_BYTE					= 0x1400
GL_UNSIGNED_BYTE		= 0x1401
GL_SHORT				= 0x1402
GL_UNSIGNED_SHORT		= 0x1403
GL_INT					= 0x1404
GL_UNSIGNED_INT			= 0x1405
GL_FLOAT				= 0x1406
GL_DOUBLE				= 0x140A

#More enable/disable modes for node objects
INTERSECTION				= -1
PICKING						= -2
DEPTH_WRITE					= -3
COLOR_WRITE					= -4
RENDERING					= -5
CULLING						= -6
PHYSICS						= -7
DISPLAY_LISTS				= -8
ANIMATIONS					= -9
EMITTERS					= -10
DYNAMICS					= -11
COLLIDE_NOTIFY				= -12
RENDER_LEFT					= -13
RENDER_RIGHT				= -14
POINT_SPRITE				= -15
SPECULAR_TEXTURE			= -16
FLIP_POLYGON_ORDER			= -17
CONTACTS					= -18
CLAMP_COLOR					= -19
FLAT_SHADING				= -20
TEXTURE_FREE_MEMORY			= -21
TEXTURE_RESIZE_NPOT	 		= -22
VERTEX_BUFFER_OBJECTS	  	= -23
TEXTURE_SHADOW				= -24
RENDER_NODE_MAIN_PASS		= -25
VERTEX_COLOR_LIGHTING		= -26
SHADOW_CASTING				= -27
INTERSECT_INFO_OBJECT		= -28
EFFECT_COMPOSITION			= -29
SHADOWS						= -30
ADJUST_AUTO_CLIP			= -31
HARDWARE_SKINNING			= -32
SWITCH_CHILD				= -33
SWITCH_ONLY_CHILD			= -34
SWITCH_ALL_CHILDREN			= -35
PROTECTED_LIGHTING			= -36
TEXTURE_SRGB				= -37
RENDER_NODE_INHERIT_CLIP_PLANE	= -38
RENDER_NODE_PROJECTION_OVERRIDE	= -39
RENDER_NODE_PROJECTION_INHERIT	= -40
SPATIALIZED_SOUND			= -41
SPATIALIZED_ATTENUATION		= -44
TEXTURE_STEREO_TOPBOTTOM	= -45
TEXTURE_STEREO_SIDEBYSIDE	= -46
TEXTURE_360_EQUIRECT		= -47
TEXTURE_360_EAC				= -48
TRIANGULATE_POLYGON			= -49

#Attribute modes that can be used for clearing
ATTR_TEXTURE			= -100
ATTR_POLYMODE			= -101
ATTR_ZOFFSET			= -102
ATTR_COLOR				= -103
ATTR_POINTSIZE			= -104
ATTR_LINEWIDTH			= -105
ATTR_DRAWORDER			= -106
ATTR_TEXCOMBINE			= -107
ATTR_TEXGEN				= -108
ATTR_TEXMAT				= -109
ATTR_DEPTHFUNC			= -110
ATTR_BLENDFUNC			= -111
ATTR_SHADER				= -112
ATTR_CLIPPLANE			= -113
ATTR_VERTEXPROGRAM		= -114
ATTR_FRAGMENTPROGRAM	= -115
ATTR_FOG				= -116
ATTR_ALL				= -117
ATTR_STENCILFUNC		= -118
ATTR_CULLFACE			= -119
ATTR_ALPHAFUNC			= -120
ATTR_BLENDCOLOR			= -121
ATTR_VERTEXCOLOR		= -122
ATTR_VERTEXNORMAL		= -123
ATTR_EFFECT				= -124
ATTR_EFFECTCOMPOSER		= -125
ATTR_UNIFORM			= -126
ATTR_COMPOSITEALPHA		= -127

#Different types of textures
_VIZ_TEX_TEX	= 0	#Normal texture
_VIZ_VID_TEX	= 1	#Video texture
_VIZ_DEL_TEX	= 3 #Remove Texture

#Texture Filter parameters
MIN_FILTER	= 0
MAG_FILTER	= 1

#Texture Wrap parameters
WRAP_S		= 0
WRAP_T		= 1
WRAP_R		= 2
WRAP_ALL	= 3

#Texture Face parameters for CubeMapped textures
POSITIVE_X	= 0
NEGATIVE_X	= 1
POSITIVE_Y	= 2
NEGATIVE_Y	= 3
POSITIVE_Z	= 4
NEGATIVE_Z	= 5

#Texture types
TEX_1D				= 0
TEX_2D				= 1
TEX_3D				= 2
TEX_CUBE			= 3
TEX_RECT			= 4
TEX_2D_MULTISAMPLE	= 5
TEX_2D_ARRAY		= 6

#Fastest expiration time for timer events
FASTEST_EXPIRATION	= 0.0

#Default delay for avatar animations
AVATAR_DELAY = 0.2

#Common Colors
WHITE				= (1,1,1)
BLACK				= (0,0,0)
GRAY				= (0.5,0.5,0.5)
RED					= (1,0,0)
GREEN				= (0,1,0)
BLUE				= (0,0,1)
YELLOW				= (1,1,0)
MAGENTA				= (1,0,1)
CYAN				= (0,1,1)
ORANGE				= (1,0.5,0)
VIOLET				= (0.5,0,1)
AZURE				= (0,0.5,1)
ROSE				= (1,0,0.5)
CHARTREUSE_GREEN	= (0.5,1,0)
SPRING_GREEN		= (0,1,0.5)
PURPLE				= (0.5,0,0.5)
SKYBLUE				= (0.5,0.5,1)
ORANGE_RED			= (1,0.27,0)
YELLOW_ORANGE		= (1,0.75,0)
SLATE				= (0.21, 0.22, 0.24)

#Color modes
COLOR_DIFFUSE			= 0
COLOR_SPECULAR			= 1
COLOR_AMBIENT			= 2
COLOR_EMISSIVE			= 3
COLOR_SHININESS			= 4
COLOR_PARTICLE_BEGIN	= 5
COLOR_PARTICLE_END		= 6
COLOR_VERTEX			= 7
COLOR_BACKDROP			= 8
COLOR_INACTIVE			= 9
COLOR_HOVER				= 10

#Child flags for checkbox
CHECKBOX_DOWN			= "checkbox_down"
CHECKBOX_UP				= "checkbox_up"
CHECKBOX_DOWN_ACTIVE	= "checkbox_down_active"
CHECKBOX_UP_ACTIVE		= "checkbox_up_active"
CHECKBOX_DOWN_INACTIVE	= "checkbox_down_inactive"
CHECKBOX_UP_INACTIVE	= "checkbox_up_inactive"

#Chid flags for slider
SLIDER_TICK				= "slider_tick"
SLIDER_BAR				= "slider_bar"
SLIDER_BAR_FILL			= "slider_bar_fill"
SLIDER_BAR_EMPTY		= "slider_bar_empty"
SLIDER_TICK_ACTIVE		= "slider_tick_active"
SLIDER_TICK_INACTIVE	= "slider_tick_inactive"
SLIDER_BAR_ACTIVE		= "slider_bar_active"
SLIDER_BAR_INACTIVE		= "slider_bar_inactive"

#Child flags for progress bar
PROGRESS_BAR_BORDER		= '0'
PROGRESS_BAR_FORE		= '1'
PROGRESS_BAR_BACK		= '2'
PROGRESS_BAR_TEXT		= '3'
PROGRESS_BAR_TEXT_FORE	= '4'
PROGRESS_BAR_TEXT_BACK	= '5'

#Child flags for textbox
TEXTBOX_BORDER			= '0'
TEXTBOX_BACK			= '1'
TEXTBOX_TEXT			= '2'
TEXTBOX_CURSOR			= '3'
TEXTBOX_BORDER_FOCUS	= '4'

#Child flags for button label
BUTTON_BORDER_DOWN		= '0'
BUTTON_BACK_DOWN		= '1'
BUTTON_TEXT_DOWN		= '2'
BUTTON_BORDER_UP		= '3'
BUTTON_BACK_UP			= '4'
BUTTON_TEXT_UP			= '5'
BUTTON_TEXT				= '6'

#Child flags for droplist
DROPLIST_BORDER			= '0'
DROPLIST_BACK			= '1'
DROPLIST_TEXT			= '2'
DROPLIST_BACK_SEL		= '3'
DROPLIST_TEXT_SEL		= '4'

#Child flags for tab group
TABGROUP_BORDER			= '0'
TABGROUP_BACK			= '1'
TABGROUP_TEXT			= '2'
TABGROUP_BACK_SEL		= '3'
TABGROUP_TEXT_SEL		= '4'

#Physics shape types
SHAPE_BOX			= 0
SHAPE_SPHERE		= 1
SHAPE_PLANE			= 2
SHAPE_MESH			= 3
SHAPE_CUSTOM		= 4

#Physics material flags
_PHYSICS_FRICTION		= 1
_PHYSICS_DENSITY		= 2
_PHYSICS_HARDNESS		= 3
_PHYSICS_BOUNCE			= 4

#Physics axis parameters
_PHYSICS_AXIS_ANGLE		= 5
_PHYSICS_AXIS_DIST		= 6
_PHYSICS_AXIS_VEL		= 7

#Physics joint types
JOINT_HINGE				= 1
JOINT_UNIVERSAL			= 2
JOINT_BALL				= 3
JOINT_SLIDER			= 4
JOINT_WHEEL				= 5
JOINT_FIXED				= 6

#Physics joint break modes
JOINT_UNBREAKABLE		= 0
JOINT_BREAK_THRESH		= 1
JOINT_BREAK_ACCUM		= 2

# Add objects
SCENE				= DeprecateObject(0)
#ENVIRONMENT_MAP	= 1 #Already defined as appearance flag
WINDOW				= DeprecateObject(2)
TEXT3D				= DeprecateObject(3)
MAILBOX				= DeprecateObject(4)
CHECKBOX			= DeprecateObject(5)
SLIDER				= DeprecateObject(6)
BUTTON				= DeprecateObject(7)
NETWORK				= DeprecateObject(8)
TEXQUAD				= DeprecateObject(9)
LIGHT				= DeprecateObject(10)
GROUP				= DeprecateObject(11)
ANIMATION_PATH		= DeprecateObject(12)
CONTROL_POINT		= DeprecateObject(13)
RADIO				= DeprecateObject(14)
VIEWPOINT			= DeprecateObject(15)
TEXTBOX				= DeprecateObject(16)
PROGRESS_BAR		= DeprecateObject(17)
BUTTON_LABEL		= DeprecateObject(18)
DROPLIST			= DeprecateObject(19)

#Possible anchors for adding objects
WORLD						= -1
HEAD						= -2
SCREEN						= -3
ORTHO						= -4
WINDOW_WORLD				= -5
WINDOW_RENDER_NODE_SCENE	= -6
DEFAULT_CANVAS				= -7
DEFAULT_CANVAS_SCREEN		= DeprecateObject(-8)

#Appearance values
ENVIRONMENT_MAP		= 0x1
TEXMODULATE			= 0x2
TEXGEN				= 0x4
TEXMIPMAP			= 0x8
TEXREPEAT			= 0x10
TEXCLAMP			= 0x20
TEXAUTOALPHA		= 0x40
TEXREPLACE			= 0x80
TEXBLEND			= 0x100
TEXDECAL			= 0x200
TEXNEAREST			= 0x400
TEXLINEAR			= 0x800
TEXADD				= 0x1000

# Texture quad display modes
TEXQUAD_STRETCH			= 0x1
TEXQUAD_FIT				= 0x2
TEXQUAD_FIXED			= 0x4
TEXQUAD_TILE			= 0x8
TEXQUAD_CORNER_FIT		= 0x10
TEXQUAD_CORNER_FIXED	= 0x20
TEXQUAD_STRETCH_HORZ	= 0x40
TEXQUAD_STRETCH_VERT	= 0x80
TEXQUAD_FILL			= 0x100

# Scene hint flags
PARTICLE_HINT				= 1
VBO_HINT					= 2
COMPRESS_TEXTURE_HINT		= 4
FREE_TEXTURE_MEMORY_HINT	= 8
ALLOW_NPOT_TEXTURE_HINT		= 16
PRELOAD_HINT				= 32
PACK_TEXCOORD_HINT			= 64
RESET_ANIMATION_HINT		= 128
TEXTURE_MODIFIED_HINT		= 256
CLEAR_PARTICLES_HINT		= 512
OPTIMIZE_INTERSECT_HINT		= 1024
COPY_SHARED_MATERIAL_HINT	= 2048
GENERATE_TANGENT_HINT		= 4096

# Model optimize flags (taken from osgUtil::Optimizer)
OPT_FLATTEN_STATIC_TRANSFORMS	= 0x1
OPT_REMOVE_REDUNDANT_NODES		= 0x2
OPT_REMOVE_LOADED_PROXY_NODES	= 0x4
OPT_COMBINE_ADJACENT_LODS		= 0x8
OPT_SHARE_DUPLICATE_STATE		= 0x10
OPT_MERGE_GEOMETRY				= 0x20
OPT_CHECK_GEOMETRY				= 0x40
OPT_MAKE_FAST_GEOMETRY			= 0x80
OPT_SPATIALIZE_GROUPS			= 0x100
OPT_COPY_SHARED_NODES			= 0x200
OPT_TRISTRIP_GEOMETRY			= 0x400
OPT_TESSELLATE_GEOMETRY			= 0x800
OPT_OPTIMIZE_TEXTURE_SETTINGS	= 0x1000
OPT_MERGE_GEODES				= 0x2000
OPT_FLATTEN_BILLBOARDS			= 0x4000
OPT_TEXTURE_ATLAS_BUILDER		= 0x8000
OPT_STATIC_OBJECT_DETECTION		= 0x10000
OPT_FLATTEN_STATIC_TRANSFORMS_DUPLICATING_SHARED_SUBGRAPHS = 0x20000
OPT_INDEX_MESH					= 0x40000
OPT_VERTEX_POSTTRANSFORM		= 0x80000
OPT_VERTEX_PRETRANSFORM			= 0x100000
OPT_ALL							= 0xffffff
OPT_DEFAULT						=	(OPT_FLATTEN_STATIC_TRANSFORMS |
									OPT_REMOVE_REDUNDANT_NODES |
									OPT_REMOVE_LOADED_PROXY_NODES |
									OPT_COMBINE_ADJACENT_LODS |
									OPT_SHARE_DUPLICATE_STATE |
									OPT_MERGE_GEOMETRY |
									OPT_MAKE_FAST_GEOMETRY |
									OPT_CHECK_GEOMETRY |
									OPT_OPTIMIZE_TEXTURE_SETTINGS |
									OPT_STATIC_OBJECT_DETECTION)

# Encoding values
ENCODING_DEFAULT	= 0
ENCODING_ASCII		= 1
ENCODING_UTF8		= 2

#Node operation bit flags
OP_DEFAULT			= -1
OP_TRAVERSE			= 4
OP_OVERRIDE			= 8
OP_ROOT				= 16
OP_NO_AUTOALPHA		= 32
OP_MATERIAL			= 64
OP_VISIBLE			= 128

#Shader bit flags
SHADER_TANGENT			= 1
SHADER_BINORMAL			= 2

#Uniform data types
UNIFORM_BOOL		= 1
UNIFORM_BOOL_VEC2	= 2
UNIFORM_BOOL_VEC3	= 3
UNIFORM_BOOL_VEC4	= 4
UNIFORM_INT			= 5
UNIFORM_INT_VEC2	= 6
UNIFORM_INT_VEC3	= 7
UNIFORM_INT_VEC4	= 8
UNIFORM_FLOAT		= 9
UNIFORM_FLOAT_VEC2	= 10
UNIFORM_FLOAT_VEC3	= 11
UNIFORM_FLOAT_VEC4	= 12
UNIFORM_FLOAT_MAT2	= 13
UNIFORM_FLOAT_MAT3	= 14
UNIFORM_FLOAT_MAT4	= 15

#Unapply flags
UNAPPLY_NODE		= 1
UNAPPLY_COMPOSER	= 2
UNAPPLY_ALL			= 0xff

#Light shadow modes
SHADOW_OFF			= 0
SHADOW_DEPTH_MAP	= 1

#Intersect operation flags
_INTERSECT_NEAREST				= 0x1
_INTERSECT_IGNORE_BACK_FACE		= 0x2
_INTERSECT_COMPUTE_PATH			= 0x4
_INTERSECT_IGNORE_CLIPPED		= 0x20

#Bounding box flags
BOUND_COMPUTE_USING_VERTICES	= 0x1

#Buffer loading modes
BUFFER_MMAP			= object()

def _getBuffer(filename,buffer):
	"""Returns buffer from filename and possible buffer mode"""
	if buffer is BUFFER_MMAP:
		fullname = res.getFullPath(filename) or filename
		file = open(fullname,'r+')
		buffer = mmap.mmap(file.fileno(), 0)
		file.close()
	return buffer

# Default port for network communication
NETWORK_PORT			= 4950

# Transform modes
ABSOLUTE		= 0
RELATIVE		= 1

ABS_PARENT		= 0
REL_PARENT		= 1
ABS_LOCAL		= 2
REL_LOCAL		= 3
ABS_GLOBAL		= 4
REL_GLOBAL		= 5

# Additional bone transformation modes
AVATAR_LOCAL		= 6
AVATAR_WORLD		= 7
ABS_PARENT_BASE		= 8
ABS_GLOBAL_BASE		= 9
AVATAR_LOCAL_BASE	= 10
AVATAR_WORLD_BASE	= 11
AVATAR_ROOT			= 12
AVATAR_ROOT_BASE	= 13

# Additional slider transformation modes
SLIDER_TICK_SIZE	= 12
SLIDER_BAR_SIZE		= 13

# Additional button transformation modes
BUTTON_SIZE			= 14

# Addition texture quad trasformations
TEXQUAD_SIZE		= 64

# Additional modes for GUI canvas node
CANVAS_CURSOR_PIXELS			= 64
CANVAS_CURSOR_NORMALIZED		= 65
CANVAS_RESOLUTION				= 66
CANVAS_CURSOR_SIZE				= 67

# View flags
VIEW_ORI			= 2
HEAD_POS			= 4
HEAD_ORI			= 8
BODY_ORI			= 16

#Possible values for "viz.get" command
HEAD_LIGHT			= DeprecateObject(-1)
VELOCITY			= DeprecateObject(-2)
BODY_EULER			= DeprecateObject(-3)
BODY_QUAT			= DeprecateObject(-4)
BODY_LOOK			= DeprecateObject(-5)
BODY_AXISANGLE		= DeprecateObject(-6)
BODY_YAW			= DeprecateObject(-7)
BODY_PITCH			= DeprecateObject(-8)
BODY_MAT			= DeprecateObject(-9)
HEAD_EULER			= DeprecateObject(-10)
HEAD_QUAT			= DeprecateObject(-11)
HEAD_LOOK			= DeprecateObject(-12)
HEAD_AXISANGLE		= DeprecateObject(-13)
HEAD_YAW			= DeprecateObject(-14)
HEAD_PITCH			= DeprecateObject(-15)
HEAD_MAT			= DeprecateObject(-16)
VIEW_EULER			= DeprecateObject(-17)
VIEW_QUAT			= DeprecateObject(-18)
VIEW_LOOK			= DeprecateObject(-19)
VIEW_AXISANGLE		= DeprecateObject(-20)
VIEW_YAW			= DeprecateObject(-21)
VIEW_PITCH			= DeprecateObject(-22)
VIEW_MAT			= DeprecateObject(-23)
MAIN_VIEWPOINT		= DeprecateObject(-24)
MAIN_WINDOW			= DeprecateObject(-25)
CLUSTER_MASK		= DeprecateObject(-26)
#CURRENT_ACTION		= -27  See below
FRAME_NUMBER		= DeprecateObject(-28)
FRAME_TIMESTAMP		= DeprecateObject(-29)
ACTION_INSTANCE		= DeprecateObject(-30)
_TIME_TICK			= -31
_THEME				= -32
_MOUSE_OVERRIDE		= -33
_COMPUTER_NAME		= -34
_COMPUTER_IP		= -35
_DONE				= -36
_NODE_LIST			= -37
_SCENE_LIST			= -38
_VIEW_LIST			= -39
_WINDOW_LIST		= -40
_VIZARD_PATH		= -41
_RESOURCE_PATH		= -42
_INPUT_TIME			= -43
_OPTION_VALUE		= -44
_OPTION_STRING		= -45
_FRAME_ELAPSED		= -46
_LIGHT_GROUP		= -47
_RADIO_GROUPS		= -48
_SELECTED_RADIO		= -49
_RADIO_BUTTONS		= -50
_RESOURCE_PATH_LIST	= -51
_TAG_DEFAULT_RENDER	= -52

# Possible values for <node3d>.clear
# (Need to be negative numbers so that <node3d:avatar>.clear can still work)
IDLE			= DeprecateObject(-1)
ACTION			= DeprecateObject(-2)
ALL				= DeprecateObject(-3)
CURRENT_ACTION	= DeprecateObject(-27) #Needs to be compatible with viz.get

# Can be used as a pool number to represent all pools
ALL_POOLS		= ''

#Possible values for <node3d>.get command
POSITION			= DeprecateObject(0)
SCALE				= DeprecateObject(1)
AXISANGLE			= DeprecateObject(2)
EULER				= DeprecateObject(3)
QUAT				= DeprecateObject(4)
LOOK				= DeprecateObject(5)
MATRIX				= DeprecateObject(6)
BOUNDING_BOX		= DeprecateObject(7)
BOUNDING_SPHERE		= DeprecateObject(8)
MESSAGE				= DeprecateObject(9)
COLOR				= DeprecateObject(10)
ALPHA				= DeprecateObject(11)
CHILDREN			= DeprecateObject(12)
PARENTS				= DeprecateObject(13)
FONT				= DeprecateObject(14)
ALIGNMENT			= DeprecateObject(15)
RESOLUTION			= DeprecateObject(16)
CENTER				= DeprecateObject(17)
VISIBLE				= DeprecateObject(18)
BILLBOARD			= DeprecateObject(19)
VERTICAL_FOV		= DeprecateObject(20)
HORIZONTAL_FOV		= DeprecateObject(21)
ASPECT_RATIO		= DeprecateObject(22)
NEAR_CLIP			= DeprecateObject(23)
FAR_CLIP			= DeprecateObject(24)
ANIMATION			= DeprecateObject(25)
FILTER_MODE			= DeprecateObject(26)
WRAP_MODE			= DeprecateObject(27)
FILENAME			= DeprecateObject(28)
COMPRESSION			= DeprecateObject(29)
TEXTURE_TYPE		= DeprecateObject(30)
VIEW				= DeprecateObject(31)
_FOCUS				= 32
LENGTH				= DeprecateObject(33)
GUI_LENGTH			= DeprecateObject(LENGTH)
_FOCUSED_NODE		= 34
ANISOTROPY			= DeprecateObject(35)
_CURSOR_POS			= 36
_SELECTION			= 37
_ITEM_COUNT			= 38
_ITEM_TEXT			= 39
_AVATAR_VARIABLE	= 40
_MORPH_VALUE		= 41
_MORPH_ID			= 42
_MORPH_NAMES		= 43
_ANIMATION_SPEED	= 44
_ANIMATION_TIME		= 45
_ANIMATION_DURATION	= 46
_AVATAR_ACTION_RUNNING = 47
_AVATAR_CYCLE_RUNNING = 48
_MESH_NAMES			= 49
_ANIMATION_NAMES	= 50
_BONE_LIST			= 51
_FACEGEOM_NAMES		= 52
_PROJMATRIX			= 53
_VID_FRAME			= 54
_VID_FRAME_COUNT	= 55
_ANGULAR_VEL		= 56
_ISCHILD			= 57
_ISPARENT			= 58
_SHAPE_MATERIAL		= 59
_SHAPE_LIST			= 60
_SHAPE_POS			= 61
_SHAPE_ROT			= 62
_SHAPE_TYPE			= 63
_BONE_AVATAR		= 64
_LINKABLE_SRC_MASK	= 65
_LINKABLE_DST_MASK	= 66
_DRAW_ORDER			= 67
_HEAD_LIGHT			= 68
_LIGHT_NUMBER		= 69
_STEREO_IPD			= 70
_STEREO_MODE		= 71
_OTF_NUMVERTS		= 72
_OTF_VERTEX			= 73
_OTF_NORMAL			= 74
_OTF_TEXCOORD		= 75
_OTF_COLOR			= 76
_VIEW_SCENE			= 77
_MEDIA_STATE		= 78
_MESH_BY_NAME		= 79
_MESH_MORPH			= 80
_MESH_MORPH_NAMES	= 81
_CLEAR_MASK			= 82
_MESH_MORPH_ID		= 83
_WINDOW_HANDLE		= 84
_NODE_MASK			= 85
_SUBNODE_NAMES		= 86
_PROXY_LINKABLE		= 87
_BLEND_LINKABLE		= 88
_SELECTED_WINDOW	= 89
_BUTTON_COUNT		= 90
_BUTTONS_STATE		= 91
_BUTTON_STATE		= 92
_TEXTURE_DATA		= 93
_PIXEL_SIZE			= 94
_MODAL_NODE			= 95
_OP_MODE			= 96
_IS_FULLSCREEN		= 97
#_FLAGGED_LINKABLE	= 98
_FLAGGED_FLAG		= 99
_PIXEL_FORMAT		= 100
_FUSION_DIST		= 101
_FUSION_DIST_MODE	= 102
_SCREEN_DIST		= 103
_VIEW_OFFSET		= 104
_VIEW_OFFSET_ORDER	= 105
_ORTHO_OFFSET		= 106
_IPD_VECTOR			= 107
_IPD_VECTOR_ORDER	= 108
_AUTO_ASPECT_RATIO	= 109
_AUTO_CLIP			= 110

# Core object types
_VIZ_OBJECT_NODE				= 1
_VIZ_OBJECT_VIEW				= 2
_VIZ_OBJECT_WINDOW				= 3
_VIZ_OBJECT_SCENE				= 4
_VIZ_OBJECT_MEDIA				= 5
_VIZ_OBJECT_ANIMATION_PATH		= 6
_VIZ_OBJECT_CONTROL_POINT		= 7
_VIZ_OBJECT_SHADER				= 8
_VIZ_OBJECT_UNIFORM				= 9
_VIZ_OBJECT_NETWORK				= 10
_VIZ_OBJECT_MAILBOX				= 11
_VIZ_OBJECT_LINK				= 12
_VIZ_OBJECT_EXT_SENSOR			= 13
_VIZ_OBJECT_EXT_OBJECT			= 14
_VIZ_OBJECT_TEXTURE				= 15
_VIZ_OBJECT_SOUND_3D			= 16
_VIZ_OBJECT_RESOURCE_CONTEXT	= 17
_VIZ_OBJECT_LINKABLE			= 18
_VIZ_OBJECT_SENSOR				= 19
_VIZ_OBJECT_EXTENSION			= 20
_VIZ_OBJECT_MODIFIER			= 21
_VIZ_OBJECT_CUSTOM_PLUGIN		= 23
_VIZ_OBJECT_EFFECT				= 25
_VIZ_OBJECT_COMPOSER			= 26
_VIZ_OBJECT_SOUND_MIXER			= 27

# Linkable types
_VIZ_NODE_LINKABLE			= 0
_VIZ_VIEW_LINKABLE			= 1
_VIZ_SENSOR_LINKABLE		= 2
_VIZ_EXTSENSOR_LINKABLE		= 3
_VIZ_PATH_LINKABLE			= 4
_VIZ_BONE_LINKABLE			= 5
_VIZ_UNIFORM_LINKABLE		= 6
_VIZ_CUSTOM_LINKABLE		= 7
_VIZ_MOUSE_LINKABLE			= 8
_VIZ_LEFT_TOP_LINKABLE		= 9
_VIZ_LEFT_CENTER_LINKABLE	= 10
_VIZ_LEFT_BOTTOM_LINKABLE	= 11
_VIZ_RIGHT_TOP_LINKABLE		= 12
_VIZ_RIGHT_CENTER_LINKABLE	= 13
_VIZ_RIGHT_BOTTOM_LINKABLE	= 14
_VIZ_CENTER_TOP_LINKABLE	= 15
_VIZ_CENTER_CENTER_LINKABLE	= 16
_VIZ_CENTER_BOTTOM_LINKALBE	= 17
_VIZ_WINDOW_SIZE_LINKABLE	= 18
_VIZ_LINK_LINKABLE			= 19
_VIZ_NULL_LINKABLE			= 20
_VIZ_WINDOW_VIEW_LINKABLE	= 21
_VIZ_CONTROL_POINT_LINKABLE	= 22
_VIZ_WINDOW_OFFSET_LINKABLE	= 23
_VIZ_SOUND_MIXER_LINKABLE	= 24
_VIZ_TEXTURE_LINKABLE		= 25

#Link masks
LINK_POS			= 1
LINK_ORI			= 2
LINK_SCALE			= 4
LINK_ALL			= 0xff

#Link axis masks
LINK_AXIS_X		= 1
LINK_AXIS_Y		= 2
LINK_AXIS_Z		= 4
LINK_AXIS_ALL	= (LINK_AXIS_X | LINK_AXIS_Y | LINK_AXIS_Z)

#Link attributes
_LINK_MASK			= 0
_LINK_SRC_MASK		= 1
_LINK_DST_MASK		= 2
_LINK_REMOVE_OP		= 3
_LINK_OFFSET		= 4
_LINK_RESET			= 5
_LINK_REMOVE		= 6
_LINK_SRC_FLAG		= 7
_LINK_DST_FLAG		= 8
_LINK_OPERATOR		= 9
_LINK_SRC			= 10
_LINK_DST			= 11
_LINK_ENABLED		= 12
_LINK_UPDATE		= 13

#Link operation types
_LINK_PRE_ROT			= 0
_LINK_POST_ROT			= 1
_LINK_PRE_TRANS			= 2
_LINK_POST_TRANS		= 3
_LINK_PRE_SCALE			= 4
_LINK_POST_SCALE		= 5
_LINK_SET_POS			= 6
_LINK_SWAP_POS			= 7
_LINK_CLAMP_POS			= 8
_LINK_SWAP_QUAT			= 9
_LINK_SET_EULER			= 10
_LINK_PRE_LINKABLE		= 11
_LINK_POST_LINKABLE		= 12
_LINK_SWAP_EULER		= 13
_LINK_PRE_INV_LINKABLE	= 14
_LINK_POST_INV_LINKABLE	= 15
_LINK_SCALE_OFFSET		= 16
_LINK_INVERT			= 17
_LINK_SCALE_EULER		= 18
_LINK_LOOK_AT			= 19
_LINK_SNAP_POS			= 20

#Link operator targets
LINK_FULL_OP		= 0
LINK_POS_OP			= 1
LINK_ORI_OP			= 2

#Link option flags
LINK_HEAD				= DeprecateObject(HEAD_ORI)
LINK_BODY				= DeprecateObject(BODY_ORI)
LINK_VIEW				= DeprecateObject(VIEW_ORI)
LINK_ABSOLUTE			= DeprecateObject(ABS_GLOBAL)
LINK_PIXELS				= DeprecateObject(WINDOW_PIXELS)
LINK_RENDERNODE_SIZE	= 64
LINK_POS_RAW			= DeprecateObject(0) #deprecated

#Link reset flags
RESET_X				= 1
RESET_Y				= 2
RESET_Z				= 4
RESET_POS			= (RESET_X | RESET_Y | RESET_Z)
RESET_ORI_LOCAL		= 8
RESET_ORI_WORLD		= 16
RESET_ORI_RAW		= 32
RESET_OPERATORS		= 64
RESET_ORI_HEADING	= 128

XAXIS				= 0
YAXIS				= 1
ZAXIS				= 2

LEFT_EYE			= 1
RIGHT_EYE			= 2
BOTH_EYE			= 3

#Window view offset modes
PRE_MULT			= 0
POST_MULT			= 1

#Node render to modes
RENDER_TO_ALL			= 0
RENDER_TO_ALL_EXCEPT	= 1
RENDER_TO_ONLY			= 2

#Node render limit modes
RENDER_LIMIT_NONE					= 0
RENDER_LIMIT_FRAME					= 1
RENDER_LIMIT_WINDOW					= 2
RENDER_LIMIT_EXCLUDE_MAIN_PASS		= 4
RENDER_LIMIT_EXCLUDE_RENDER_NODE	= 8

#Polygon render modes
POLY_WIRE			= 1
POLY_POINT			= 2
POLY_FILL			= 3

OPEN				= DeprecateObject(0)	# Curtain params
CLOSE				= DeprecateObject(1)

OFF                 = 0
ON                  = 1
TOGGLE				= -1

#Mode for framerate
NICE				= 2

#For clip plane and aspect ratio
AUTO_COMPUTE		= -1

UP					= 0
DOWN				= 1

UNCHECKED			= 0
CHECKED				= 1

START			= 0
PLAY			= 0
LOOP			= 1
STOP			= 2
PAUSE			= 3
SOUND_PRELOAD	= 4
STOP_LOOP		= 5
RESUME			= 6

#Media states
MEDIA_STOPPED	= DeprecateObject(STOP)
MEDIA_PAUSED	= DeprecateObject(PAUSE)
MEDIA_RUNNING	= DeprecateObject(PLAY)

#Media load flags
MEDIA_REQUIRE_AUDIO		= 0x20000
MEDIA_REQUIRE_VIDEO		= 0x40000
MEDIA_IGNORE_AUDIO		= 0x80000
MEDIA_IGNORE_VIDEO		= 0x100000
MEDIA_FORCE_RGB			= 0x200000

#Media type flags
MEDIA_TYPE_AUDIO				= 0x1
MEDIA_TYPE_VIDEO				= 0x2
MEDIA_TYPE_IMAGE				= 0x4
MEDIA_TYPE_SPHERICAL			= 0x8
MEDIA_TYPE_STEREO_TOPBOTTOM		= 0x10
MEDIA_TYPE_STEREO_SIDEBYSIDE	= 0x20

#Media sync flags
MEDIA_SYNC_VIDEO		= 0x2

#Media seek flags
SEEK_NEAREST_KEY_FRAME			= 0x1

#Media event codes
MEDIA_END		= 1

PERPETUAL			= -1
FOREVER				= -1

#######################################################

#Modes for translators and spinners
TIME		= DeprecateObject(0)
SPEED		= DeprecateObject(VELOCITY)

#NON ASCII KEY VALUES
###########################################################
KEY_BACKSPACE		='65288'
KEY_TAB				='65289'
KEY_RETURN			='65293'
KEY_SCROLL_LOCK		='65300'
KEY_SYS_REQ			='65301'
KEY_PRINT			='65301'
KEY_ESCAPE			='65307'
KEY_HOME			='65360'
KEY_LEFT			='65361'
KEY_UP				='65362'
KEY_RIGHT			='65363'
KEY_DOWN			='65364'
KEY_PAGE_UP			='65365'
KEY_PAGE_DOWN		='65366'
KEY_END				='65367'
KEY_INSERT			='65379'
KEY_MENU			='65383'
KEY_BREAK			='65387'
KEY_PAUSE			='65387'
KEY_NUM_LOCK		='65407'
KEY_KP_ENTER		='65421'
KEY_KP_MULTIPLY		='65450'
KEY_KP_ADD			='65451'
KEY_KP_SUBTRACT		='65453'
KEY_KP_DECIMAL		='65454'
KEY_KP_DIVIDE		='65455'
KEY_KP_0			='65456'
KEY_KP_1			='65457'
KEY_KP_2			='65458'
KEY_KP_3			='65459'
KEY_KP_4			='65460'
KEY_KP_5			='65461'
KEY_KP_6			='65462'
KEY_KP_7			='65463'
KEY_KP_8			='65464'
KEY_KP_9			='65465'
KEY_F1				='65470'
KEY_F2				='65471'
KEY_F3				='65472'
KEY_F4				='65473'
KEY_F5				='65474'
KEY_F6				='65475'
KEY_F7				='65476'
KEY_F8				='65477'
KEY_F9				='65478'
KEY_F10				='65479'
KEY_F11				='65480'
KEY_F12				='65481'
KEY_SHIFT_L			='65505'
KEY_SHIFT_R			='65506'
KEY_CONTROL_L		='65507'
KEY_CONTROL_R		='65508'
KEY_CAPS_LOCK		='65509'
KEY_ALT_L			='65513'
KEY_ALT_R			='65514'
KEY_WINDOWS_L		='65515'
KEY_WINDOWS_R		='65516'
KEY_DELETE			='65535'

#Backwards compatibility
KEY_SUPER_L = DeprecateObject(KEY_WINDOWS_L)
KEY_SUPER_R = DeprecateObject(KEY_WINDOWS_R)
KEY_PRIOR = DeprecateObject(KEY_PAGE_UP)
KEY_NEXT = DeprecateObject(KEY_PAGE_DOWN)

#Audio filter modes
FILTER_NONE				= 0
FILTER_LOWPASS			= 1
FILTER_BANDPASS			= 2
FILTER_HIGHPASS			= 3
FILTER_NOTCH			= 4

class AudioFilter(object):
	"""Defines audio filter properties"""
	def __init__(self, mode, frequency=0.0, Q=1.0):
		self.mode = mode
		self.frequency = frequency
		self.Q = Q

	def __repr__(self):
		return 'AudioFilter(mode={mode}, frequency={frequency}, Q={Q})'.format(**self.__dict__)

# Audio channels
CHANNEL_FRONT_LEFT				= 0x00000001
CHANNEL_FRONT_RIGHT				= 0x00000002
CHANNEL_FRONT_CENTER			= 0x00000004
CHANNEL_LOW_FREQUENCY			= 0x00000008
CHANNEL_BACK_LEFT				= 0x00000010
CHANNEL_BACK_RIGHT				= 0x00000020
CHANNEL_FRONT_LEFT_OF_CENTER	= 0x00000040
CHANNEL_FRONT_RIGHT_OF_CENTER	= 0x00000080
CHANNEL_BACK_CENTER				= 0x00000100
CHANNEL_SIDE_LEFT				= 0x00000200
CHANNEL_SIDE_RIGHT				= 0x00000400
CHANNEL_TOP_CENTER				= 0x00000800
CHANNEL_TOP_FRONT_LEFT			= 0x00001000
CHANNEL_TOP_FRONT_CENTER		= 0x00002000
CHANNEL_TOP_FRONT_RIGHT			= 0x00004000
CHANNEL_TOP_BACK_LEFT			= 0x00008000
CHANNEL_TOP_BACK_CENTER			= 0x00010000
CHANNEL_TOP_BACK_RIGHT			= 0x00020000
CHANNEL_ALL						= 0x000fffff
CHANNEL_ALL_LEFT				= CHANNEL_FRONT_LEFT | CHANNEL_BACK_LEFT | CHANNEL_FRONT_LEFT_OF_CENTER | CHANNEL_SIDE_LEFT | CHANNEL_TOP_FRONT_LEFT | CHANNEL_TOP_BACK_LEFT
CHANNEL_ALL_RIGHT				= CHANNEL_FRONT_RIGHT | CHANNEL_BACK_RIGHT | CHANNEL_FRONT_RIGHT_OF_CENTER | CHANNEL_SIDE_RIGHT | CHANNEL_TOP_FRONT_RIGHT | CHANNEL_TOP_BACK_RIGHT
CHANNEL_ALL_FRONT				= CHANNEL_FRONT_LEFT | CHANNEL_FRONT_RIGHT | CHANNEL_FRONT_CENTER | CHANNEL_FRONT_LEFT_OF_CENTER | CHANNEL_FRONT_RIGHT_OF_CENTER | CHANNEL_TOP_FRONT_LEFT | CHANNEL_TOP_FRONT_CENTER | CHANNEL_TOP_FRONT_RIGHT
CHANNEL_ALL_BACK				= CHANNEL_BACK_LEFT | CHANNEL_BACK_RIGHT | CHANNEL_BACK_CENTER | CHANNEL_TOP_BACK_LEFT | CHANNEL_TOP_BACK_CENTER | CHANNEL_TOP_BACK_RIGHT

###########################################################

#Scene numbers start from 0, but to be compatible with VRUT
#scene numbers need to start from 1.
#So whenever a user specifies a scene number you must subtract 1
#before sending it through ipc
MAIN_SCENE		= DeprecateObject(1)
_MAIN_VIEWPOINT	= 0

def _sceneID(scene):
	if isinstance(scene,(VizScene,VizWindow)):
		return scene.id
	return scene-1

#############################
# Cached Vizard objects
#############################

def __AddObject(d,obj):
	d[obj.id] = obj

def __GetObject(d,id,dummy):
	if id in d:
		return d[id]
	return dummy(id)

def __RemoveObject(d,id):
	if id in d:
		del d[id]

_GlobalJointList = {}
_AddJoint = lambda obj : __AddObject(_GlobalJointList,obj)
_GetJoint = lambda id : __GetObject(_GlobalJointList,id,VizPhysicsJoint)
_RemoveJoint = lambda obj : __RemoveObject(_GlobalJointList,obj)

_TypeModel = set(['WRL','3DS','OBJ','GEO','GEM','FLT','OSG','IV','IVE','LW','LWO','LWS','3DC','PLY','P3D','OGR','SHP','STL','TGZ','AC','MDL','PFB','TXP','DXF','DW','DP','BSP','OSGX','X','DAE','FBX','OSGT','OSGB','GLTF','GLB'])
_TypeImage = set(['JPG', 'JPEG', 'BMP', 'TIF', 'TIFF', 'GIF', 'PNG', 'RGB', 'RGBA','TGA', 'DDS', 'PIC', 'BMX','PNM','PPM','PGM','PBM','PVR','VTF','KTX','WEBP','KTX2','BASIS'])
_TypeAudio = set(['WAV', 'MP3', 'MID', 'MIDI','AU', 'WMA'])
_TypeVideo = set(['AVI', 'MPG', 'MPEG', 'WMV', 'MOV', 'ASF'])
_TypeAvatar = set(['CFG'])
_TypeFace = set(['VZF'])

def done():
	"""Returns whether the the simulation is finished"""
	return _ipcSend(_VIZ_GET,_DONE,0,'',0.0,0.0,0.0,0.0)

def frame():
	"""Manually update the frame"""
	_ipcSend(_VIZ_UPDATEFRAME,0,0,'',0.0,0.0,0.0,0.0)

def update(flag,elapsed=0.0):
	"""Manually trigger internal update tasks"""
	_ipcSend(_VIZ_UPDATEFRAME,1,flag,'',elapsed,0.0,0.0,0.0)

def endMainLoop():
	"""End the main loop for embedded applications"""
	_ipcSend(_VIZ_UPDATEFRAME,2,0,'',0.0,0.0,0.0,0.0)

def setDisplayMode(width,height,color=0,frequency=0):
	"""Change the display mode. Must be called before viz.go()"""
	setOption('viz.display.width',width)
	setOption('viz.display.height',height)
	setOption('viz.display.color',color)
	setOption('viz.display.frequency',frequency)

def setMultiSample(samples):
	"""Set fullscreen anti-aliasing samples. Must be called before viz.go()"""
	setOption('viz.antialias',samples)

class _ResourceInterface(object):
	"""For internal use only"""
	def getVizardPath(self):
		"""Return the Vizard directory path"""
		return _ipcSend(_VIZ_GET,_VIZARD_PATH,0,'',0.0,0.0,0.0,0.0)

	def getFullPath(self, filename):
		"""Get the full path of a resource"""
		p = _ipcSend(_VIZ_GET,_RESOURCE_PATH,0,filename,0.0,0.0,0.0,0.0)
		if p:
			p = os.path.abspath(p)
		return p

	def setFileLoaderOption(self, option):
		"""Set option string for file loaders"""
		_ipcSend(_VIZ_RESOURCESET,0,0,option,0.0,0.0,0.0,0.0)

	def getFileLoaderOption(self):
		"""Get option string for file loaders"""
		return _ipcSend(_VIZ_GET,_OPTION_STRING,0,'',0.0,0.0,0.0,0.0)

	def addPath(self, path):
		"""Add a directory to the resource path"""
		_ipcSend(_VIZ_RESOURCESET,2,0,path,0.0,0.0,0.0,0.0)

	def removePath(self, path):
		"""Remove a directory from the resource path (case-sensitive)"""
		_ipcSend(_VIZ_RESOURCESET,3,0,path,0.0,0.0,0.0,0.0)

	def setPathList(self, paths):
		"""Set the resource path list"""
		_ipcSend(_VIZ_RESOURCESET,1,0,';'.join(paths),0.0,0.0,0.0,0.0)

	def getPathList(self):
		"""Get the resource path list"""
		return _ipcSend(_VIZ_GET,_RESOURCE_PATH_LIST,0,'',0.0,0.0,0.0,0.0)

	def addPublishFile(self, filename):
		"""Add a file to the publish resource list"""
		_ipcSend(_VIZ_RESOURCESET,4,0,filename,0.0,0.0,0.0,0.0)

	def addPublishDirectory(self, directory, pattern='*'):
		"""Recursively add all files in a directory to the publish resource list"""
		import fnmatch
		def _process(dir,pattern):
			for f in os.listdir(dir):
				path = os.path.join(dir,f)
				if os.path.isdir(path) and not os.path.islink(path):
					_process(path,pattern)
				elif fnmatch.fnmatch(f, pattern):
					_ipcSend(_VIZ_RESOURCESET,4,0,path,0.0,0.0,0.0,0.0)
		_process(os.path.abspath(directory),pattern)

	def addPublishFileLoader(self, ext):
		"""Add the file loader for the specified extension to the publish resource list"""
		_ipcSend(_VIZ_RESOURCESET,5,0,ext,0.0,0.0,0.0,0.0)

	def addPublishImageLoaders(self):
		"""Add the image loader for all common image types to the publish resource list"""
		for ext in ('bmp','dds','gif','jpeg','png','tga','tif','webp'):
			_ipcSend(_VIZ_RESOURCESET,5,0,ext,0.0,0.0,0.0,0.0)

	def getPublishedPath(self, filename=''):
		"""Returns full path of file in published executable directory"""
		publishPath = getOption('viz.publish.path','')
		if publishPath:
			return os.path.join(publishPath,filename)
		return filename

	def addPublishFilter(self, filter):
		"""Add a string or callback function for filtering files from published resource list
		Callback function should return True if file should be filtered from publish list, or False if it should be kept."""
		if callable(filter):
			_publishFilters.append(filter)
		else:

			import fnmatch
			def _filterfunc(filename):
				return fnmatch.fnmatch(filename, filter)

			_publishFilters.append(_filterfunc)

	def isCapturing(self):
		"""Returns whether resources are being captured (i.e. when publishing to an exe)"""
		return getOption('viz.publishing',0,type=int)

	def isPublished(self):
		"""Returns whether the script is running in published mode (i.e. within an exe)"""
		return getOption('viz.publish',0,type=int)

_publishFilters = []

res = _ResourceInterface()

def setCollectRenderStats(mode, token=''):
	"""Set whether rendering stats should be collected"""
	_ipcSend(_VIZ_STATSSET,1,mode,token,0.0,0.0,0.0,0.0)

def getRenderStats():
	"""Get render stats from last frame.
	Must first enable stats collection using viz.setCollectRenderStats()"""
	return RenderStats(*_ipcSend(_VIZ_SCENESTATS,2,0,'',0.0,0.0,0.0,0.0))

def setOption(name, value):
	"""Set the value of an option. If the value is None the option will be removed"""
	if value is None:
		_ipcSend(_VIZ_SETOPTION,1,0,name,0.0,0.0,0.0,0.0)
	else:
		if isinstance(value, bool):
			value = int(value)
		_ipcSend(_VIZ_SETSTRING,0,0,str(value),0.0,0.0,0.0,0.0)
		_ipcSend(_VIZ_SETOPTION,0,0,name,0.0,0.0,0.0,0.0)

def getOption(name,default='',type=None):
	"""Get the value of an option. If the option does not exist 'default' will be returned"""
	val = _ipcSend(_VIZ_GET,_OPTION_VALUE,0,name,0.0,0.0,0.0,0.0)
	if val is None:
		val = default
	if type is not None:
		try:
			return type(val)
		except (ValueError,TypeError):
			return default
	return val

def log(level, *args, **kw):
	"""Log a message"""
	message = kw.get('sep',' ').join((str(x) for x in args)) + kw.get('end','\n')
	_ipcSend(_VIZ_LOGMESSAGE,0,level,message,0.0,0.0,0.0,0.0)

def logAlways(*args,**kw):
	"""Log a message at the highest level"""
	log(LOG_ALWAYS,*args,**kw)

def logError(*args,**kw):
	"""Log an error message"""
	log(LOG_ERROR,*args,**kw)

def logWarn(*args,**kw):
	"""Log a warning message"""
	log(LOG_WARN,*args,**kw)

def logNotice(*args,**kw):
	"""Log a notice message"""
	log(LOG_NOTICE,*args,**kw)

def logInfo(*args,**kw):
	"""Log an info message"""
	log(LOG_INFO,*args,**kw)

def logDebug(*args,**kw):
	"""Log a debug message"""
	log(LOG_DEBUG,*args,**kw)

def logStatus(*args,**kw):
	"""Log a status message"""
	log(LOG_STATUS,*args,**kw)

def logSplash(*args,**kw):
	"""Log a splash screen message"""
	log(LOG_SPLASH,*args,**kw)

def logNull(*args,**kw):
	"""Discards log messages"""
	pass

def setLogLevel(level):
	"""Set output level of log messages"""
	return _ipcSend(_VIZ_LOGSET,0,level,'',0.0,0.0,0.0,0.0)

def setLogFile(filename):
	"""Set file to log all output to"""
	return _ipcSend(_VIZ_LOGMESSAGE,1,0,filename,0.0,0.0,0.0,0.0)

class LogLevelContext(object):
	"""Class that implements context manager protocol for pushing/popping log level"""
	def __init__(self, level):
		self._level = level

	def __enter__(self):
		self._prevLevel = setLogLevel(self._level)

	def __exit__(self,exc_type, exc_val, exc_tb):
		setLogLevel(self._prevLevel)

class SplashContext(object):
	"""Class that implements context manager protocol for logging message to splash and clearing when finished"""
	def __init__(self, *args, **kw):
		self._args = args
		self._kwargs = kw

	def __enter__(self):
		log(LOG_SPLASH, *self._args, **self._kwargs)

	def __exit__(self,exc_type, exc_val, exc_tb):
		log(LOG_SPLASH, '')

class SplashGroupContext(object):
	"""Class that implements context manager protocol for logging a group of splash messages"""
	def __init__(self, *args, **kw):
		self._args = args
		self._kwargs = kw

	def __enter__(self):
		log(LOG_SPLASH_BEGIN_GROUP, *self._args, **self._kwargs)

	def __exit__(self,exc_type, exc_val, exc_tb):
		log(LOG_SPLASH_END_GROUP, '')

class SplashOverrideContext(object):
	"""Class that implements context manager protocol for overriding splash message"""
	def __init__(self, *args, **kw):
		self._args = args
		self._kwargs = kw

	def __enter__(self):
		log(LOG_SPLASH_BEGIN_OVERRIDE, *self._args, **self._kwargs)

	def __exit__(self,exc_type, exc_val, exc_tb):
		log(LOG_SPLASH_END_OVERRIDE, '')

#************************************************************
def go(mode = 0, window=0):
	"""Start the graphics window in the given mode"""

	_ipcSend(_VIZ_GO,mode,window,'',0.0,0.0,0.0,0.0)

	if mode & ACTKERN:
		#Create actkern class timer which creates a graphical mouse pointer
		_actkernTexture = addTexture('mouse.png',filter=NEAREST)
		_actkernQuad = addTexQuad(ORTHO)
		_actkernQuad.setScale(64,64,1)
		_actkernQuad.texture(_actkernTexture)
		_actkernQuad.drawOrder(99999)
		link(Mouse,_actkernQuad,srcFlag=WINDOW_PIXELS)
		mouse.setVisible(OFF)

def setTheme(theme, notify=True, node=None):
	"""Set the color theme for GUI objects"""
	mode = 0
	if node is not None:
		mode = 1
	theme._apply(mode)
	if node is not None:
		_ipcSend(_VIZ_SETTHEMECOLOR,-2,node.id,'',0.0,0.0,0.0,0.0)
	elif notify:
		_ipcSend(_VIZ_SETTHEMECOLOR,-1,0,'',0.0,0.0,0.0,0.0)

def getTheme():
	"""Return the current color theme for GUI objects"""
	return Theme(_ipcSend(_VIZ_GET,_THEME,0,'',0.0,0.0,0.0,0.0))

class EventClass(object):
	"""A class that can register itself to handle Vizard events"""

	_VizObjectCache = {}

	@classmethod
	def _GetObject(cls,id):
		"""INTERNAL USE ONLY"""
		return cls._VizObjectCache.get(id,None)

	@classmethod
	def _RemoveObject(cls,id):
		"""INTERNAL USE ONLY"""
		if id in cls._VizObjectCache:
			obj = cls._VizObjectCache[id]
			obj._eventClassRemoved()
			obj.__classID = -1
			del cls._VizObjectCache[id]

	def __init__(self):
		self.__classID = _ipcSend(_VIZ_REGISTERCLASS,0,0,'',0.0,0.0,0.0,0.0)

		#Add object to base class cache
		if self.__classID > -1:
			EventClass._VizObjectCache[self.__classID] = self

	def _eventClassRemoved(self):
		"""Called when the event class is removed"""
		pass

	def _onSetActive(self, active):
		"""Called when the active state of the event class is modified"""
		pass

	def unregister(self):
		"""Unregister the EventClass with ALL events"""
		_ipcSend(_VIZ_REGISTERCLASS,-1,self.__classID,'',0.0,0.0,0.0,0.0)
		self.__classID = -1

	def callback(self, event, function, priority = PRIORITY_DEFAULT):
		"""Register the EventClass with the event type"""
		_ipcSendCallback(event,function,0,self.__classID,priority)

	def starttimer(self, timerNum = 1, timeSec = FASTEST_EXPIRATION, repeat = 0):
		"""Start a timer that will only expire for the EventClass"""
		_ipcSend(_VIZ_STARTTIMER,timerNum,repeat,'',timeSec,self.__classID,0.0,0.0)

	def killtimer(self,timerNum):
		"""Kill a timer that was started for the EventClass"""
		_ipcSend(_VIZ_KILLTIMER,timerNum,self.__classID,'',0.0,0.0,0.0,0.0)

	def setEnabled(self,mode):
		"""Enable/disable event class"""
		_ipcSend(_VIZ_SETEVTHANDLER,self.__classID,1,'',mode,0.0,0.0,0.0)

	def getEnabled(self):
		"""Get whether the event class is enabled"""
		return _ipcSend(_VIZ_SETEVTHANDLER,self.__classID,2,'',0.0,0.0,0.0,0.0)

	def addWindowMessage(self,msg):
		"""Add a window message to handle"""
		_ipcSend(_VIZ_SETEVTHANDLER,self.__classID,3,'',msg,0.0,0.0,0.0)

	def removeWindowMessage(self,msg):
		"""Remove a window message to handle"""
		_ipcSend(_VIZ_SETEVTHANDLER,self.__classID,4,'',msg,0.0,0.0,0.0)

	def clearWindowMessages(self):
		"""Remove a window message to handle"""
		_ipcSend(_VIZ_SETEVTHANDLER,self.__classID,5,'',0.0,0.0,0.0,0.0)

class VizEventTarget(object):
	"""Base class for event target objects"""

	def addEventCallback(self, event, func, priority=PRIORITY_DEFAULT):
		"""Added event callback to object"""
		return _ipcSendAddTargetCallback(self.id, self._VizObjectType, event, func, priority)

	def removeEventCallback(self, event, func):
		"""Remove event callback from object"""
		return _ipcSendRemoveTargetCallback(self.id, self._VizObjectType, event, func)

	def sendEvent(self, event, *args):
		"""Send event to all object callbacks"""
		return _ipcSendTargetEvent(self.id, self._VizObjectType, event, args)

class VizActor(object):
	"""A class that creates an interface for performing asynchronous actions on an object"""
	def __init__(self):
		self._action = None

	def removeActor(self):
		"""Permanently remove the actor"""
		if self._action:
			self._action.remove()
			self._action = None

	def addAction(self,action,pool=0):
		"""Add an action to the object"""
		if not self._action:
			self._action = ActionController(self)
		self._action.addAction(action,pool)

	def addIdle(self,action,pool=0):
		"""Add an action to the objects idle list"""
		if not self._action:
			self._action = ActionController(self)
		self._action.addIdle(action,pool)

	def runAction(self,action,pool=0):
		"""Runs an action on the object immediately"""
		if not self._action:
			self._action = ActionController(self)
		self._action.runAction(action,pool)

	def startAction(self,pool=0):
		"""Starts the next action in the pool"""
		if self._action:
			self._action.startAction(pool)

	def endAction(self,pool=0):
		"""End an action running on a pool"""
		if self._action:
			self._action.endAction(pool)

	def clearActionList(self,pool=0):
		"""Clear pending actions"""
		if self._action:
			self._action.clearActionList(pool)

	def clearIdleList(self,pool=0):
		"""Clear pending idle actions"""
		if self._action:
			self._action.clearIdleList(pool)

	def clearActions(self,pool=0):
		"""Clear queued and running actions on pool"""
		if self._action:
			self._action.clearPool(pool)

	def pauseActions(self,pool=0):
		"""Pause an action pool"""
		if self._action:
			self._action.pauseActions(True,pool)

	def resumeActions(self,pool=0):
		"""Resume an action pool"""
		if self._action:
			self._action.pauseActions(False,pool)

	def getAction(self,pool=0):
		"""Return the current action being performed on the given pool"""
		if self._action:
			return self._action.getAction(pool)
		return None

	def getActionInstance(self,pool=0):
		"""Return the current action instance being performed on the given pool"""
		if self._action:
			return self._action.getActionInstance(pool)
		return None

class VizObject(Removable):
	"""A class that encapsulates a core Vizard object using an integer ID"""

	_VizObjectType = -1

	@classmethod
	def _GetObject(cls,id,*args,**kw):
		"""INTERNAL USE ONLY"""
		if id in cls._VizObjectCache:
			return cls._VizObjectCache[id]
		return cls(id,*args,**kw)

	@classmethod
	def _RemoveObject(cls,id):
		"""INTERNAL USE ONLY"""
		if id in cls._VizObjectCache:
			obj = cls._VizObjectCache[id]
			obj.__class__._OnRemoveObject(obj)
			obj.id = -1
			del cls._VizObjectCache[id]

	@classmethod
	def _OnRemoveObject(cls,obj):
		"""INTERNAL USE ONLY"""
		if isinstance(obj,VizActor):
			obj.removeActor()
		obj._notifyRemoveCallbacks()

	def __init__(self, id, base=None):
		self.id = int(id)

		if base is not None:
			EmitDeprecationWarning('"base" argument is not used and will be removed in future versions')

		# Add object to base class cache, if it exists
		if self.id > -1 and hasattr(self.__class__, '_VizObjectCache'):
			self.__class__._VizObjectCache[self.id] = self

	def __repr__(self):
		return '%s.%s(%d)'%(self.__class__.__module__,self.__class__.__name__,self.id)

	def __eq__(self, other):
		if isinstance(other, VizObject):
			if self._VizObjectType == other._VizObjectType:
				if self._VizObjectType == -1 and not isinstance(other, self.__class__):
					return NotImplemented
				return self.id == other.id
		return NotImplemented

	def __hash__(self):
		return self.id

	def __bool__(self):
		return self.id > -1

	def __int__(self):
		return self.id

	def valid(self):
		return self.id > -1

class VizResourceContext(VizObject):
	"""VizResourceContext object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_RESOURCE_CONTEXT

	#Used for generating unique ID for every resource context that is created
	_contextCounter = 1

	def __init__(self, id):
		VizObject.__init__(self, id)

		#Save contextID that is used for hash value
		self.contextID = VizResourceContext._contextCounter
		VizResourceContext._contextCounter += 1

	def __hash__(self):
		return self.contextID

	def __enter__(self):
		self.push()

	def __exit__(self,exc_type, exc_val, exc_tb):
		self.pop()

	def remove(self):
		"""Permanently delete the resource context and all nested resources"""
		_ipcSend(_VIZ_RESCONTEXTSET,1,self.id,'',0.0,0.0,0.0,0.0)

	def push(self):
		"""Push the resource context on top of the current context stack"""
		_ipcSend(_VIZ_RESCONTEXTSET,2,self.id,'',0.0,0.0,0.0,0.0)

	def pop(self):
		"""Pop the resource context from the top of the stack"""
		_ipcSend(_VIZ_RESCONTEXTSET,3,self.id,'',0.0,0.0,0.0,0.0)

	def setEnabled(self,mode):
		"""Set enabled mode of resource context. Can use viz.TOGGLE to toggle state"""
		_ipcSend(_VIZ_RESCONTEXTSET,4,self.id,'',mode,0.0,0.0,0.0)

	def enable(self): self.setEnabled(True)
	def disable(self): self.setEnabled(False)

	def getEnabled(self):
		"""Get enabled mode of resource context, True/False"""
		return _ipcSend(_VIZ_RESCONTEXTGET,2,self.id,'',0.0,0.0,0.0,0.0)

MainResourceContext = VizResourceContext(0)

class VizLinkable(VizObject):
	"""VizLinkable object"""

	_VizLinkableType = -1

	def __init__(self, id, linkType=None, base=None):
		VizObject.__init__(self, id)
		if linkType is not None:
			self._VizLinkableType = linkType
		if base is not None:
			EmitDeprecationWarning('"base" argument is not used and will be removed in future versions')

	def getSrcMask(self):
		"""Get source mask of linkable"""
		return _ipcSend(_VIZ_LINKABLE_GET,_LINKABLE_SRC_MASK,self.id,'',self._VizLinkableType,0.0,0.0,0.0)

	def getDstMask(self):
		"""Get source mask of linkable"""
		return _ipcSend(_VIZ_LINKABLE_GET,_LINKABLE_DST_MASK,self.id,'',self._VizLinkableType,0.0,0.0,0.0)

	def getPosition(self,flag=0):
		"""Return position of linkable"""
		return _ipcSend(_VIZ_LINKABLE_GET,POSITION,self.id,'',self._VizLinkableType,flag,0.0,0.0)

	def getScale(self,flag=0):
		"""Return scale of linkable"""
		return _ipcSend(_VIZ_LINKABLE_GET,SCALE,self.id,'',self._VizLinkableType,flag,0.0,0.0)

	def getQuat(self,flag=0):
		"""Return quaternion rotation of linkable"""
		return _ipcSend(_VIZ_LINKABLE_GET,QUAT,self.id,'',self._VizLinkableType,flag,0.0,0.0)

	def getAxisAngle(self,flag=0):
		"""Return axisangle rotation of linkable"""
		return _ipcSend(_VIZ_LINKABLE_GET,AXISANGLE,self.id,'',self._VizLinkableType,flag,0.0,0.0)

	def getEuler(self,flag=0):
		"""Return euler rotation of linkable"""
		return _ipcSend(_VIZ_LINKABLE_GET,EULER,self.id,'',self._VizLinkableType,flag,0.0,0.0)

	def getMatrix(self,flag=0):
		"""Return transform matrix of linkable"""
		return Transform(_ipcSend(_VIZ_LINKABLE_GET,MATRIX,self.id,'',self._VizLinkableType,flag,0.0,0.0))

	def getLineForward(self, flag=0, length=1.0):
		"""Return Line object starting at linkable position and ending at specified length along forward vector"""
		return Line(_ipcSend(_VIZ_LINKABLE_GET,LOOK,self.id,'',self._VizLinkableType,flag,length,0.0))

	def setPosition(self,pos,flag=0):
		"""Set position of linkable"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', pos[0], pos[1], pos[2], 0.0)
		_ipcSend(_VIZ_LINKABLESET,self.id,POSITION,'',self._VizLinkableType,flag,0.0,0.0)

	def setScale(self,scale,flag=0):
		"""Set scale of linkable"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', scale[0], scale[1], scale[2], 0.0)
		_ipcSend(_VIZ_LINKABLESET,self.id,SCALE,'',self._VizLinkableType,flag,0.0,0.0)

	def setQuat(self,quat,flag=0):
		"""Set quaternion rotation of linkable"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', quat[0], quat[1], quat[2], quat[3])
		_ipcSend(_VIZ_LINKABLESET,self.id,QUAT,'',self._VizLinkableType,flag,0.0,0.0)

	def setAxisAngle(self,axisAngle,flag=0):
		"""Set axisangle rotation of linkable"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', axisAngle[0], axisAngle[1], axisAngle[2], axisAngle[3])
		_ipcSend(_VIZ_LINKABLESET,self.id,AXISANGLE,'',self._VizLinkableType,flag,0.0,0.0)

	def setEuler(self,euler,flag=0):
		"""Set euler rotation of linkable"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', euler[0], euler[1], euler[2], 0.0)
		_ipcSend(_VIZ_LINKABLESET,self.id,EULER,'',self._VizLinkableType,flag,0.0,0.0)

	def setMatrix(self,matrix,flag=0):
		"""Set transform matrix of linkable"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', matrix[0], matrix[1], matrix[2], matrix[3])
		_ipcSend(_VIZ_SETMATRIX2, 0, 0, '', matrix[4], matrix[5], matrix[6], matrix[7])
		_ipcSend(_VIZ_SETMATRIX3, 0, 0, '', matrix[8], matrix[9], matrix[10], matrix[11])
		_ipcSend(_VIZ_SETMATRIX4, 0, 0, '', matrix[12], matrix[13], matrix[14], matrix[15])
		_ipcSend(_VIZ_LINKABLESET,self.id,MATRIX,'',self._VizLinkableType,flag,0.0,0.0)

	def resetMatrix(self, mask=LINK_ALL, flag=0):
		"""Reset transform matrix of linkable"""
		_ipcSend(_VIZ_LINKABLESET,self.id,_CLEAR_MASK,'',self._VizLinkableType,mask,flag,0.0)

	def lookAt(self, point, roll=0.0, flag=0):
		"""Set the rotation of the linkable to look at the specified point"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', point[0], point[1], point[2], roll)
		_ipcSend(_VIZ_LINKABLESET,self.id,LOOK,'',self._VizLinkableType,flag,0.0,0.0)

class VizCustomLinkable(VizLinkable):
	"""Linkable object that has unique ID assigned to it"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_LINKABLE
	_VizLinkableType = _VIZ_CUSTOM_LINKABLE

	def __init__(self, id):
		VizLinkable.__init__(self, id)

class VizMergeLinkable(VizCustomLinkable):
	"""Class that merges a position and orientation linkable into one linkable object"""
	def setPosLinkable(self,pos):
		"""Set the position linkable object"""
		posType = _getLinkableType(pos)
		if posType < 0:
			raise TypeError('Position object is not a linkable type')
		_ipcSend(_VIZ_LINKABLESET,self.id,_PROXY_LINKABLE,'',pos.id,posType,0,0.0)

	def setOriLinkable(self,ori):
		"""Set the orientation linkable object"""
		oriType = _getLinkableType(ori)
		if oriType < 0:
			raise TypeError('Orientation object is not a linkable type')
		_ipcSend(_VIZ_LINKABLESET,self.id,_PROXY_LINKABLE,'',ori.id,oriType,1,0.0)

	def getPosLinkable(self):
		"""Get the position linkable object"""
		id,type = _ipcSend(_VIZ_LINKABLE_GET,_PROXY_LINKABLE,self.id,'',0,0.0,0.0,0.0)
		return _getLinkableObj(id,type)

	def getOriLinkable(self):
		"""Get the orientation linkable object"""
		id,type = _ipcSend(_VIZ_LINKABLE_GET,_PROXY_LINKABLE,self.id,'',1,0.0,0.0,0.0)
		return _getLinkableObj(id,type)

class VizFlagWrappedLinkable(VizCustomLinkable):
	"""Class that wraps get/set functions of linkable with a specified flag"""
	def setFlag(self,flag):
		"""Set flag to use when accessing wrapped linkable"""
		_ipcSend(_VIZ_LINKABLESET,self.id,_FLAGGED_FLAG,'',flag,0.0,0.0,0.0)

	def getFlag(self):
		"""Return flag that is used when accessing wrapped linkable"""
		return _ipcSend(_VIZ_LINKABLE_GET,_FLAGGED_FLAG,self.id,'',0.0,0.0,0.0,0.0)

	def setLinkable(self,linkable):
		"""Set linkable to wrap access to"""
		linkableType = _getLinkableType(linkable)
		if linkableType < 0:
			raise TypeError('Object is not a linkable type')
		_ipcSend(_VIZ_LINKABLESET,self.id,_PROXY_LINKABLE,'',linkable.id,linkableType,0.0,0.0)

	def getLinkable(self):
		"""Return the linkable that is being wrapped with flag"""
		id,type = _ipcSend(_VIZ_LINKABLE_GET,_PROXY_LINKABLE,self.id,'',0.0,0.0,0.0,0.0)
		return _getLinkableObj(id,type)

class VizBlendLinkable(VizCustomLinkable):
	"""Class that blends between a begin and end linkable by a specified blend percentage"""
	def setBeginLinkable(self, begin):
		"""Set the begin linkable object"""
		beginType = _getLinkableType(begin)
		if beginType < 0:
			raise TypeError('Begin object is not a linkable type')
		_ipcSend(_VIZ_LINKABLESET,self.id,_PROXY_LINKABLE,'',begin.id,beginType,0,0.0)

	def setEndLinkable(self, end):
		"""Set the end linkable object"""
		endType = _getLinkableType(end)
		if endType < 0:
			raise TypeError('End object is not a linkable type')
		_ipcSend(_VIZ_LINKABLESET,self.id,_PROXY_LINKABLE,'',end.id,endType,1,0.0)

	def getBeginLinkable(self):
		"""Get the begin linkable object"""
		id,type = _ipcSend(_VIZ_LINKABLE_GET,_PROXY_LINKABLE,self.id,'',0,0.0,0.0,0.0)
		return _getLinkableObj(id,type)

	def getEndLinkable(self):
		"""Get the end linkable object"""
		id,type = _ipcSend(_VIZ_LINKABLE_GET,_PROXY_LINKABLE,self.id,'',1,0.0,0.0,0.0)
		return _getLinkableObj(id,type)

	def setBlend(self, blend, mask=LINK_ALL):
		"""Set the blend percentage"""
		_ipcSend(_VIZ_LINKABLESET,self.id,_BLEND_LINKABLE,'',blend,mask,0.0,0.0)

	def getBlend(self, mask=LINK_ALL):
		"""Get the blend percentage"""
		return _ipcSend(_VIZ_LINKABLE_GET,_BLEND_LINKABLE,self.id,'',mask,0.0,0.0,0.0)

class VizMailbox(VizObject):
	"""VizMailbox object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_MAILBOX

	def __init__(self, id):
		VizObject.__init__(self, id)

	def remove(self):
		"""Delete the mailbox object"""
		_ipcSend(_VIZ_DELNETWORK,self.id,1,'',0.0,0.0,0.0,0.0)

	def send(self,message):
		"""Send a string to the mailbox"""
		_ipcSend(_VIZ_SENDMAIL,self.id,0,message,0.0,0.0,0.0,0.0)

class VizModifier(VizObject):
	"""VizModifier object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_MODIFIER

	def __init__(self, id):
		VizObject.__init__(self, id)

	def get(self):
		"""Retrieve data from the modifier"""
		return _ipcSend(_VIZ_GETMODIFIER,self.id,0,'',0.0,0.0,0.0,0.0)

	def command(self,command,mesg='',x=0.0,y=0.0,z=0.0,w=0.0):
		"""Send a command to the modifier"""
		_ipcSend(_VIZ_COMMANDMOD,self.id,command,mesg,x,y,z,w)

class VizSensor(VizLinkable):
	"""VizSensor object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_SENSOR
	_VizLinkableType = _VIZ_SENSOR_LINKABLE

	def __init__(self, id):
		VizLinkable.__init__(self, id)

	def command(self, issuedCommand, message = '', a=0.0, b=0.0, c=0.0, d=0.0):
		"""Send a command to the sensor"""
		_ipcSend(_VIZ_COMMANDPLUGIN,self.id,0,message,issuedCommand,a,b,c)

	def reset(self):
		"""Send the reset command to the sensor"""
		_ipcSend(_VIZ_RESETPLUGIN,self.id,0,'',0.0,0.0,0.0,0.0)

	def getData(self):
		"""Retrieve data from the sensor"""
		return _ipcSend(_VIZ_GETPLUGIN,POSITION,self.id,'',0.0,0.0,0.0,0.0)
	get = getData

	def getName(self):
		"""Get the name of the sensor"""
		return _ipcSend(_VIZ_GETPLUGIN,MESSAGE,self.id,'',0.0,0.0,0.0,0.0)

	def getFilename(self):
		"""Get the filename of the sensor"""
		return _ipcSend(_VIZ_GETPLUGIN,FILENAME,self.id,'',0.0,0.0,0.0,0.0)

class VizPPT(VizSensor):

	def scale(self,x,y='',z=''):
		"""Scale the movement"""
		if _islist(x):
			self.command(3,'',x[0],x[1],x[2])
		elif isinstance(y,str):
			self.command(3,'',x,x,x)
		else:
			self.command(3,'',x,y,z)

	def smooth(self,samples):
		"""Smooth data over certain number of samples"""
		self.command(5,'',samples)

	def resetmask(self,x=1,y=1,z=1):
		"""Set which axis is affected by the reset command"""
		if _islist(x):
			self.command(6,'',x[0],x[1],x[2])
		else:
			self.command(6,'',x,y,z)

	def center(self,x,y=0,z=0):
		"""Recenter the ppt data around the given location"""
		if _islist(x):
			self.command(7,'',x[0],x[1],x[2])
		else:
			self.command(7,'',x,y,z)

upgradeSensor('vizppt',VizPPT)

class VizRenderer(VizSensor):
	"""VizRenderer object"""
	pass

class VizScene(VizObject):
	"""VizScene object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_SCENE

	def __init__(self, id):
		VizObject.__init__(self, id)

	def remove(self):
		"""Permanently delete the viewpoint"""
		_ipcSend(_VIZ_SCENEREMOVE,self.id,0,'',0.0,0.0,0.0,0.0)

	def getStats(self):
		"""Returns scene statistics"""
		return NodeStats(*_ipcSend(_VIZ_SCENESTATS,1,self.id,'',0.0,0.0,0.0,0.0))

	def enable(self, mode, op=OP_DEFAULT,parent=WORLD):
		"""Enable the given GL mode"""
		_ipcSend(_VIZ_SETSCENEMODE,self.id,mode,'',1,op,parent,0.0)

	def disable(self, mode, op=OP_DEFAULT,parent=WORLD):
		"""disable the given GL mode"""
		_ipcSend(_VIZ_SETSCENEMODE,self.id,mode,'',0,op,parent,0.0)

	def hint(self, flag):
		"""Set hint flags for rendering the scene"""
		_ipcSend(_VIZ_HINTSCENE,self.id,0,'',flag,0.0,0.0,0.0)

	def visible(self, state, mode=0):
		"""Set whether the scene should be rendered"""
		_ipcSend(_VIZ_SCENEVISIBLE,self.id,state,'',mode,0.0,0.0,0.0)

	def modify(self, modifier, command = 0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0):
		"""Send the scene to the given modifier"""
		if isinstance(modifier,VizModifier):
			_ipcSend(_VIZ_MODIFYPARAMS,modifier.id,command,mesg,x,y,z,w)
			_ipcSend(_VIZ_MODIFYSCENE,modifier.id,self.id,'',0.0,0.0,0.0,0.0)

	def fogColor(self, red, green=0, blue=0):
		"""Set the color of fog"""
		if _islist(red):
			_ipcSend(_VIZ_SETFOGCOLOR,self.id,0,'',red[0],red[1],red[2],1.0)
		else:
			_ipcSend(_VIZ_SETFOGCOLOR,self.id,0,'',red,green,blue,1.0)

	def fog(self, start, end = 0):
		"""Enable fog for the scene"""
		if end > 0:
			mode = LINEAR
			density = 1
		else:
			if end == 0:
				mode = EXP
			else:
				mode = EXP2
			density = start

		_ipcSend(_VIZ_SETFOGMODE, self.id, mode, '', start, end, density, 0.0)

	def intersect(self, lineBegin, lineEnd, all=False, ignoreBackFace=False, computePath=False, ignoreClipped=False, radius=0):
		"""intersect(lineBegin,lineEnd)
		Perform an intersection on the world with a line
		specified by 'lineBegin' and 'lineEnd'.
		This will return an Intersect object
		@return Intersect()"""

		flag = 0
		if not all:
			flag |= _INTERSECT_NEAREST
		if ignoreBackFace:
			flag |= _INTERSECT_IGNORE_BACK_FACE
		if computePath:
			flag |= _INTERSECT_COMPUTE_PATH
		if ignoreClipped:
			flag |= _INTERSECT_IGNORE_CLIPPED

		_ipcSend(_VIZ_SETLINEBEGIN,0,0,'',lineBegin[0],lineBegin[1],lineBegin[2],radius)

		return _ipcSend(_VIZ_SCENEINTERSECT,self.id,0,'',lineEnd[0],lineEnd[1],lineEnd[2],flag)

	def getChildren(self, mode=WORLD, all=False):
		"""Get children of scene"""
		results = _ipcSend(_VIZ_SCENEGET,CHILDREN,self.id,'',mode,all,0.0,0.0)
		return [ _GetNode(id) for id in results ]

	@DeprecateObject
	def add(self,what,*args,**kw):
		"""Add an object to the scene"""
		if isinstance(what,int):
			if what == TEXT3D:
				return addText(args[0],scene=self,*(args[1:]),**kw)
			elif what == TEXQUAD:
				return addTexQuad(scene=self,*args,**kw)
			elif what == GROUP:
				return addGroup(scene=self,*args,**kw)
			elif what == LIGHT:
				return addLight(scene=self,*args,**kw)
			elif what == SLIDER:
				return addSlider(self,*args,**kw)
			elif what == CHECKBOX:
				return addCheckbox(self,*args,**kw)
			elif what == BUTTON:
				return addButton(self,*args,**kw)
			elif what == RADIO:
				return addRadioButton(args[0],self,*(args[1:]),**kw)
			elif what == TEXTBOX:
				return addTextbox(self,*args,**kw)
			elif what == PROGRESS_BAR:
				return addProgressBar(args[0],self,*(args[1:]),**kw)
			elif what == BUTTON_LABEL:
				return addButtonLabel(args[0],self,*(args[1:]),**kw)
			elif what == DROPLIST:
				return addDropList(self,*args,**kw)
			else:
				raise ValueError('Unrecognized add type: '+str(what))
		else:

			fileType = _getFileExtension(what).upper()

			# VRMLs
			if fileType in _TypeModel:
				return addChild(what,scene=self,*args,**kw)

			# Avatar
			elif fileType in _TypeAvatar:
				return addAvatar(what,scene=self,*args,**kw)

			# Custom child plug-in
			elif fileType == 'DLC':
				return addCustomNode(what,scene=self,*args,**kw)

			# Viz Face File
			elif fileType in _TypeFace:
				return addFace(what,scene=self,*args,**kw)

			else:
				raise ValueError('Unrecognized file extension: '+fileType)

#Create initial six scene objects
MainScene = Scene1 = VizScene(0)
Scene2 = VizScene(1)
Scene3 = VizScene(2)
Scene4 = VizScene(3)
Scene5 = VizScene(4)
Scene6 = VizScene(5)

class VizViewOri(VizActor):
	def __init__(self,id,mask):
		VizActor.__init__(self)
		self.id = id
		self.mask = mask

	def __eq__(self, other):
		if isinstance(other, VizViewOri):
			return self.id == other.id and self.mask == other.mask
		return NotImplemented

	def __hash__(self):
		return self.id

	def __bool__(self):
		return self.id > -1

	def __int__(self):
		return self.id

	def valid(self):
		return self.id > -1

	def getPosition(self, mode = ABS_PARENT):
		"""Get position of view ori"""
		return _ipcSend(_VIZ_VIEWGET,POSITION,self.id,'',0.0,0.0,0.0,0.0)

	def getEuler(self, mode = ABS_PARENT):
		"""Get euler of view ori"""
		return _ipcSend(_VIZ_VIEWGET,EULER,self.id,'',self.mask,0.0,0.0,0.0)

	def getAxisAngle(self, mode = ABS_PARENT):
		"""Get axis angle of view ori"""
		return _ipcSend(_VIZ_VIEWGET,AXISANGLE,self.id,'',self.mask,0.0,0.0,0.0)

	def getQuat(self, mode = ABS_PARENT):
		"""Get quaternion of view ori"""
		return _ipcSend(_VIZ_VIEWGET,QUAT,self.id,'',self.mask,0.0,0.0,0.0)

	def getMatrix(self, mode = ABS_PARENT):
		"""Get matrix of view ori"""
		return Transform(_ipcSend(_VIZ_VIEWGET,MATRIX,self.id,'',self.mask,0.0,0.0,0.0))

	def setPosition(self, x, y=ABSOLUTE, z=0, mode = ABSOLUTE):
		"""Translate the view ori"""
		if _islist(x):
			_ipcSend(_VIZ_TRANSVIEW,self.id,y,'',x[0],x[1],x[2],self.mask)
		else:
			_ipcSend(_VIZ_TRANSVIEW,self.id,mode,'',x,y,z,self.mask)

	def setEuler(self, x, y=ABSOLUTE, z=0, mode = ABSOLUTE):
		"""Set euler rotation of view ori"""
		if _islist(x):
			_ipcSend(_VIZ_ROTEULERVIEW,self.id,self.mask,'',x[0],x[1],x[2],y)
		else:
			_ipcSend(_VIZ_ROTEULERVIEW,self.id,self.mask,'',x,y,z,mode)

	def setAxisAngle(self, x, y=ABSOLUTE, z=0, deg=0, mode = ABSOLUTE):
		"""Rotate the view ori"""
		if _islist(x):
			_ipcSend(_VIZ_ROTAXISVIEW,self.id,self.mask,str(y),x[0],x[1],x[2],x[3])
		else:
			_ipcSend(_VIZ_ROTAXISVIEW,self.id,self.mask,str(mode),x,y,z,deg)

	def setQuat(self, x, y=ABSOLUTE, z=0, w=0, mode=ABSOLUTE):
		"""Rotate the view ori using quaternions"""
		if _islist(x):
			_ipcSend(_VIZ_ROTQUATVIEW,self.id,self.mask,str(y),x[0],x[1],x[2],x[3])
		else:
			_ipcSend(_VIZ_ROTQUATVIEW,self.id,self.mask,str(mode),x,y,z,w)

	def setMatrix(self, transform, mode = ABSOLUTE):
		"""Set the 4x4 matrix of the view ori"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', transform[0], transform[1], transform[2], transform[3])
		_ipcSend(_VIZ_SETMATRIX2, 0, 0, '', transform[4], transform[5], transform[6], transform[7])
		_ipcSend(_VIZ_SETMATRIX3, 0, 0, '', transform[8], transform[9], transform[10], transform[11])
		_ipcSend(_VIZ_SETMATRIX4, 0, 0, '', transform[12], transform[13], transform[14], transform[15])
		_ipcSend(_VIZ_SETVIEWMATRIX,self.id,self.mask,'',mode,0.0,0.0,0.0)

class VizView(VizObject,VizActor):
	"""VizViewpoint object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_VIEW
	_VizLinkableType = _VIZ_VIEW_LINKABLE

	@classmethod
	def _OnRemoveObject(cls,obj):
		"""INTERNAL USE ONLY"""
		for o in obj._oriCache.values():
			o.removeActor()
			o.id = -1
		VizObject._OnRemoveObject(obj)

	def __init__(self, id, scene=None):
		VizActor.__init__(self)
		VizObject.__init__(self, id)
		self._oriCache = {}

		if self.valid():
			if scene is not None:
				self.setScene(scene)

	def remove(self):
		"""Permanently delete the viewpoint"""
		_ipcSend(_VIZ_VIEWREMOVE,self.id,0,'',0.0,0.0,0.0,0.0)

	def getOri(self,mask):
		"""Get handle to orientation of viewpoint"""
		if mask in self._oriCache:
			return self._oriCache[mask]
		return self._oriCache.setdefault(mask,VizViewOri(self.id,mask))

	def getBody(self):
		"""Get handle to body orientation"""
		return self.getOri(BODY_ORI)

	def getHead(self):
		"""Get handle to head orientation"""
		return self.getOri(HEAD_ORI)

	def add(self,action,pool=0):
		"""Add an action to the viewpoint"""
		self.addAction(action,pool)

	def setScene(self, scene, eye = BOTH_EYE):
		"""Set the scene associated with the view"""
		_ipcSend(_VIZ_SETSCENE,self.id,_sceneID(scene),'',eye,0.0,0.0,0.0)

	def reset(self, what):
		"""Reset the given attributes of the view"""
		_ipcSend(_VIZ_RESET,self.id,what,'',0.0,0.0,0.0,0.0)

	def getPosition(self, mode = ABS_PARENT):
		"""Get position of viewpoint"""
		return _ipcSend(_VIZ_VIEWGET,POSITION,self.id,'',0.0,0.0,0.0,0.0)

	def getEuler(self, mask = VIEW_ORI):
		"""Get euler of viewpoint"""
		return _ipcSend(_VIZ_VIEWGET,EULER,self.id,'',mask,0.0,0.0,0.0)

	def getAxisAngle(self, mask = VIEW_ORI):
		"""Get axis angle of viewpoint"""
		return _ipcSend(_VIZ_VIEWGET,AXISANGLE,self.id,'',mask,0.0,0.0,0.0)

	def getQuat(self, mask = VIEW_ORI):
		"""Get quaternion of viewpoint"""
		return _ipcSend(_VIZ_VIEWGET,QUAT,self.id,'',mask,0.0,0.0,0.0)

	def getMatrix(self, mask = VIEW_ORI):
		"""Get matrix of viewpoint"""
		return Transform(_ipcSend(_VIZ_VIEWGET,MATRIX,self.id,'',mask,0.0,0.0,0.0))

	def getLineForward(self, mask=VIEW_ORI, length=1.0):
		"""Return Line object starting at linkable position and ending at specified length along forward vector"""
		return Line(_ipcSend(_VIZ_LINKABLE_GET,LOOK,self.id,'',self._VizLinkableType,mask,length,0.0))

	def getHeadLight(self):
		"""Get head light of viewpoint"""
		return VizLight(_ipcSend(_VIZ_VIEWGET,_HEAD_LIGHT,self.id,'',0.0,0.0,0.0,0.0))

	def getScene(self, eye = LEFT_EYE):
		"""Get the current scene associated with the view"""
		return VizScene._GetObject(_ipcSend(_VIZ_VIEWGET,_VIEW_SCENE,self.id,'',eye,0.0,0.0,0.0))

	@DeprecateObject
	def lookat(self,x, y=0, z=HEAD_ORI, roll = 0, mask = HEAD_ORI):
		"""Have the view look at a given point"""
		if _islist(x):
			#x is a list, so y becomes roll and z becomes mask
			_ipcSend(_VIZ_VIEWLOOKAT,self.id,z,'',x[0],x[1],x[2],y)
		else:
			_ipcSend(_VIZ_VIEWLOOKAT,self.id,mask,'',x,y,z,roll)

	def lookAt(self, point, roll=0.0, mask=HEAD_ORI):
		"""Set the rotation of the view to look at the specified point"""
		_ipcSend(_VIZ_VIEWLOOKAT,self.id,mask,'',point[0],point[1],point[2],roll)

	def setPosition(self, x, y=ABSOLUTE, z=0, mode = ABSOLUTE, mask = VIEW_ORI):
		"""Translate the view"""
		if _islist(x):
			_ipcSend(_VIZ_TRANSVIEW,self.id,y,'',x[0],x[1],x[2],mask)
		else:
			_ipcSend(_VIZ_TRANSVIEW,self.id,mode,'',x,y,z,mask)

	def setEuler(self, x, y=HEAD_ORI, z=ABSOLUTE, mask = HEAD_ORI, mode = ABSOLUTE):
		"""Set euler rotation of view"""
		if _islist(x):
			_ipcSend(_VIZ_ROTEULERVIEW,self.id,y,'',x[0],x[1],x[2],z)
		else:
			_ipcSend(_VIZ_ROTEULERVIEW,self.id,mask,'',x,y,z,mode)

	def setAxisAngle(self, x, y=HEAD_ORI, z=ABSOLUTE, deg='', mask = HEAD_ORI, mode = ABSOLUTE):
		"""Rotate the view"""
		if _islist(x):
			_ipcSend(_VIZ_ROTAXISVIEW,self.id,y,str(z),x[0],x[1],x[2],x[3])
		else:
			_ipcSend(_VIZ_ROTAXISVIEW,self.id,mask,str(mode),x,y,z,deg)

	def setQuat(self,x,y=HEAD_ORI,z=ABSOLUTE,w=0, mask = HEAD_ORI, mode = ABSOLUTE):
		"""Rotate the view using quaternions"""
		if _islist(x):
			_ipcSend(_VIZ_ROTQUATVIEW,self.id,y,str(z),x[0],x[1],x[2],x[3])
		else:
			_ipcSend(_VIZ_ROTQUATVIEW,self.id,mask,str(mode),x,y,z,w)

	def setMatrix(self, transform, mask = HEAD_ORI, mode = ABSOLUTE):
		"""Set the 4x4 matrix of the view"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', transform[0], transform[1], transform[2], transform[3])
		_ipcSend(_VIZ_SETMATRIX2, 0, 0, '', transform[4], transform[5], transform[6], transform[7])
		_ipcSend(_VIZ_SETMATRIX3, 0, 0, '', transform[8], transform[9], transform[10], transform[11])
		_ipcSend(_VIZ_SETMATRIX4, 0, 0, '', transform[12], transform[13], transform[14], transform[15])
		_ipcSend(_VIZ_SETVIEWMATRIX,self.id,mask,'',mode,0.0,0.0,0.0)

	def resetMatrix(self, mask=LINK_ALL, mode=ABSOLUTE):
		"""Reset transform matrix of view"""
		_ipcSend(_VIZ_LINKABLESET,self.id,_CLEAR_MASK,'',self._VizLinkableType,mask,mode,0.0)

	def eyeheight(self, height, immediate = ON):
		"""Set the eyeheight of the view"""
		_ipcSend(_VIZ_EYEHEIGHT,self.id,immediate,'',height,0.0,0.0,0.0)

	def gravity(self,value):
		"""Set the gravity of the view, used with collision detections"""
		_ipcSend(_VIZ_SETGRAVITY,self.id,0,'',value,0.0,0.0,0.0)

	def stepSize(self,value):
		"""Set the stepsize of the view, used with collision detections"""
		_ipcSend(_VIZ_SETSTEPSIZE,self.id,0,'',value,0.0,0.0,0.0)

	def collisionBuffer(self,value):
		"""Set the collision detection buffer of the view"""
		_ipcSend(_VIZ_COLLIDEBUFFER,self.id,0,'',value,0.0,0.0,0.0)

	def collision(self,value = ON):
		"""Turn collision ON or OFF of the view"""
		_ipcSend(_VIZ_ENABLECOLLIDE,self.id,value,'',0.0,0.0,0.0,0.0)

	def moveRelative(self,state):
		"""Set the orientation that all movement will be relative to"""
		_ipcSend(_VIZ_MOVERELATIVE,self.id,state,'',0.0,0.0,0.0,0.0)

	def move(self,side, up = VIEW_ORI, forward = 0, mask = VIEW_ORI):
		"""Move the view"""
		if _islist(side):
			_ipcSend(_VIZ_MOVE,self.id,up,'',side[0],side[1],side[2],0.0)
		else:
			_ipcSend(_VIZ_MOVE,self.id,mask,'',side,up,forward,0.0)

	def velocity(self,vx, vy = RELATIVE, vz = 0, mode = RELATIVE):
		"""Set the velocity of the view"""
		if _islist(vx):
			_ipcSend(_VIZ_SETVELOCITY,self.id,vy,'',vx[0],vx[1],vx[2],0.0)
		else:
			_ipcSend(_VIZ_SETVELOCITY,self.id,mode,'',vx,vy,vz,0.0)

MainView = VizView(0)

class VizWindow(VizObject):
	"""VizWindow object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_WINDOW

	def __init__(self, id, pos=None, size=None, clip=None, fov=None, view=None, clearcolor=None, order=None, clearMask=None, scene=None):
		VizObject.__init__(self, id)

		# Create window linkable objects
		self.LeftTop			= VizLinkable(id, _VIZ_LEFT_TOP_LINKABLE)
		self.LeftCenter			= VizLinkable(id, _VIZ_LEFT_CENTER_LINKABLE)
		self.LeftBottom			= VizLinkable(id, _VIZ_LEFT_BOTTOM_LINKABLE)
		self.RightTop			= VizLinkable(id, _VIZ_RIGHT_TOP_LINKABLE)
		self.RightCenter		= VizLinkable(id, _VIZ_RIGHT_CENTER_LINKABLE)
		self.RightBottom		= VizLinkable(id, _VIZ_RIGHT_BOTTOM_LINKABLE)
		self.CenterTop			= VizLinkable(id, _VIZ_CENTER_TOP_LINKABLE)
		self.CenterCenter		= VizLinkable(id, _VIZ_CENTER_CENTER_LINKABLE)
		self.CenterBottom		= VizLinkable(id, _VIZ_CENTER_BOTTOM_LINKALBE)
		self.WindowSize			= VizLinkable(id, _VIZ_WINDOW_SIZE_LINKABLE)
		self.WindowView			= VizLinkable(id, _VIZ_WINDOW_VIEW_LINKABLE)
		self.WindowViewOffset	= VizLinkable(id, _VIZ_WINDOW_OFFSET_LINKABLE)

		if self.valid():
			if pos is not None:
				self.setPosition(pos)
			if size is not None:
				self.setSize(size)
			if clip is not None:
				self.clip(clip)
			if fov is not None:
				self.fov(fov)
			if view is not None:
				self.setView(view)
			if clearcolor is not None:
				self.clearcolor(clearcolor)
			if order is not None:
				self.drawOrder(order)
			if clearMask is not None:
				self.setClearMask(clearMask)
			if scene is not None:
				self.setScene(scene)

	def remove(self):
		"""Permanently delete the window"""
		_ipcSend(_VIZ_WINDOWREMOVE,self.id,0,'',0.0,0.0,0.0,0.0)

	def getPosition(self,mode=WINDOW_NORMALIZED):
		"""Get position of window"""
		return _ipcSend(_VIZ_WINDOWGET,POSITION,self.id,'',mode,0.0,0.0,0.0)

	def getSize(self,mode=WINDOW_NORMALIZED):
		"""Get size of window"""
		return _ipcSend(_VIZ_WINDOWGET,SCALE,self.id,'',mode,0.0,0.0,0.0)

	def getVisible(self,mode=0):
		"""Get visibility of window"""
		return _ipcSend(_VIZ_WINDOWGET,VISIBLE,self.id,'',mode,0.0,0.0,0.0)

	def getVerticalFOV(self,eye=BOTH_EYE):
		"""Get vertical FOV of window"""
		return _ipcSend(_VIZ_WINDOWGET,VERTICAL_FOV,self.id,'',eye,0.0,0.0,0.0)

	def getHorizontalFOV(self,eye=BOTH_EYE):
		"""Get horizontal FOV of window"""
		return _ipcSend(_VIZ_WINDOWGET,HORIZONTAL_FOV,self.id,'',eye,0.0,0.0,0.0)

	def getAspectRatio(self,eye=BOTH_EYE):
		"""Get aspect ratio of window"""
		return _ipcSend(_VIZ_WINDOWGET,ASPECT_RATIO,self.id,'',eye,0.0,0.0,0.0)

	def getNearFarClip(self, eye=BOTH_EYE):
		"""Get (near,far) clip plane of window"""
		return _ipcSend(_VIZ_WINDOWGET,NEAR_CLIP,self.id,'',eye,0.0,0.0,0.0)

	@DeprecateObject
	def getNearClip(self,eye=BOTH_EYE):
		"""Get near clip plane of window"""
		return self.getNearFarClip(eye)[0]

	@DeprecateObject
	def getFarClip(self,eye=BOTH_EYE):
		"""Get far clip plane of window"""
		return self.getNearFarClip(eye)[1]

	def getProjectionMatrix(self,eye=BOTH_EYE):
		"""Get projection matrix of window"""
		return Transform(_ipcSend(_VIZ_WINDOWGET,_PROJMATRIX,self.id,'',eye,0.0,0.0,0.0))

	def getMatrix(self,eye=BOTH_EYE):
		"""Get view matrix of window"""
		return Transform(_ipcSend(_VIZ_WINDOWGET,MATRIX,self.id,'',eye,0.0,0.0,0.0))

	def getView(self):
		"""Get the current viewpoint of the window"""
		return VizView._GetObject(_ipcSend(_VIZ_WINDOWGET,VIEW,self.id,'',0.0,0.0,0.0,0.0))

	def getChildren(self, mode=ORTHO, all=False):
		"""Get children nodes of window ortho"""
		results = _ipcSend(_VIZ_WINDOWGET,CHILDREN,self.id,'',mode,all,0.0,0.0)
		return [ _GetNode(id) for id in results ]

	def getDrawOrder(self):
		"""Return draw order of window"""
		return _ipcSend(_VIZ_WINDOWGET,_DRAW_ORDER,self.id,'',0.0,0.0,0.0,0.0)

	def getStereo(self):
		"""Return stereo mode of window"""
		return _ipcSend(_VIZ_WINDOWGET,_STEREO_MODE,self.id,'',0.0,0.0,0.0,0.0)

	def getStereoSwap(self):
		"""Get whether left/right eyes should be swapped during stereo rendering"""
		return _ipcSend(_VIZ_WINDOWGET,117,self.id,'',0.0,0.0,0.0,0.0)

	def getIPD(self):
		"""Return stereo ipd of window"""
		return _ipcSend(_VIZ_WINDOWGET,_STEREO_IPD,self.id,'',0.0,0.0,0.0,0.0)

	def getIPDVector(self):
		"""Get stereo IPD vector"""
		return _ipcSend(_VIZ_WINDOWGET,_IPD_VECTOR,self.id,'',0.0,0.0,0.0,0.0)

	def getIPDVectorMultOrder(self):
		"""Get multiplication order for stereo IPD vector"""
		return _ipcSend(_VIZ_WINDOWGET,_IPD_VECTOR_ORDER,self.id,'',0.0,0.0,0.0,0.0)

	def getScreenDistance(self):
		"""Return screen distance of window"""
		return _ipcSend(_VIZ_WINDOWGET,_SCREEN_DIST,self.id,'',0.0,0.0,0.0,0.0)

	def getFusionDistance(self):
		"""Return fusion distance of window"""
		return _ipcSend(_VIZ_WINDOWGET,_FUSION_DIST,self.id,'',0.0,0.0,0.0,0.0)

	def getFusionDistanceMode(self):
		"""Return fusion distance mode of window"""
		return _ipcSend(_VIZ_WINDOWGET,_FUSION_DIST_MODE,self.id,'',0.0,0.0,0.0,0.0)

	def getViewOffset(self,eye=BOTH_EYE):
		"""Return view offset matrix of window"""
		return Transform(_ipcSend(_VIZ_WINDOWGET,_VIEW_OFFSET,self.id,'',eye,0.0,0.0,0.0))

	def getViewOffsetMultOrder(self,eye=BOTH_EYE):
		"""Return view offset matrix multiplication order of window"""
		return _ipcSend(_VIZ_WINDOWGET,_VIEW_OFFSET_ORDER,self.id,'',eye,0.0,0.0,0.0)

	@DeprecateObject
	def getOrthoOffset(self):
		"""Get the pixel offset for ortho graphic nodes in stereo"""
		return _ipcSend(_VIZ_WINDOWGET,_ORTHO_OFFSET,self.id,'',0.0,0.0,0.0,0.0)

	def getCropRect(self, mode=WORLD, eye=BOTH_EYE):
		"""Get the (left,bottom,right,top) crop rectangle for the window projection matrix"""
		return _ipcSend(_VIZ_WINDOWGET,115,self.id,'',mode,eye,0.0,0.0)

	def getAutoAspectRatio(self):
		"""Return whether aspect ratio is automatically computed based on window size"""
		return _ipcSend(_VIZ_WINDOWGET,_AUTO_ASPECT_RATIO,self.id,'',0.0,0.0,0.0,0.0)

	def getAutoClip(self):
		"""Get whether clip planes will be auto computed based on scene content"""
		return _ipcSend(_VIZ_WINDOWGET,_AUTO_CLIP,self.id,'',0.0,0.0,0.0,0.0)

	def getClearColor(self):
		"""Get clear color of window"""
		return _ipcSend(_VIZ_WINDOWGET,COLOR,self.id,'',0.0,0.0,0.0,0.0)

	def getClearMask(self):
		"""Return the clear mask of the window"""
		return _ipcSend(_VIZ_WINDOWGET,_CLEAR_MASK,self.id,'',0.0,0.0,0.0,0.0)

	def getCullMask(self,eye=BOTH_EYE):
		"""Get cull mask of window"""
		return _ipcSend(_VIZ_WINDOWGET,_NODE_MASK,self.id,'',eye,0.0,0.0,0.0)

	def drawOrder(self,order):
		"""Set the draw order of the window"""
		_ipcSend(_VIZ_WINDOWORDER,self.id,order,'',0.0,0.0,0.0,0.0)

	def frustum(self,left,right,bottom,top,near,far,eye=BOTH_EYE):
		"""Specify a perspective view frustum for the window"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', left,right,bottom,top)
		_ipcSend(_VIZ_WINSETFRUSTUM,self.id,0,'',near,far,0.0,eye)

	def ortho(self,left,right,bottom,top,near,far,eye=BOTH_EYE):
		"""Specify an orthographic view frustum for the window"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', left,right,bottom,top)
		_ipcSend(_VIZ_WINSETFRUSTUM,self.id,1,'',near,far,0.0,eye)

	def setProjectionMatrix(self, matrix, eye=BOTH_EYE, preserveClip=False):
		"""Set the projection matrix of the window"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', matrix[0], matrix[1], matrix[2], matrix[3])
		_ipcSend(_VIZ_SETMATRIX2, 0, 0, '', matrix[4], matrix[5], matrix[6], matrix[7])
		_ipcSend(_VIZ_SETMATRIX3, 0, 0, '', matrix[8], matrix[9], matrix[10], matrix[11])
		_ipcSend(_VIZ_SETMATRIX4, 0, 0, '', matrix[12], matrix[13], matrix[14], matrix[15])
		_ipcSend(_VIZ_WINSETFRUSTUM,self.id,2,'',preserveClip,0.0,0.0,eye)

	def setAutoClip(self, autoClip, maxFarPlane=AUTO_COMPUTE):
		"""Set whether clip planes will be auto computed"""
		_ipcSend(_VIZ_WINDOWSET,self.id,8,'',autoClip,maxFarPlane,0.0,0.0)

	def clip(self, near, far=1000,eye=BOTH_EYE):
		"""Set the near,far clipping range of the window"""
		if _islist(near):
			_ipcSend(_VIZ_CLIP,self.id,eye,'',near[0],near[1],0.0,0.0)
		else:
			_ipcSend(_VIZ_CLIP,self.id,eye,'',near,far,0.0,0.0)

	def fov(self, vertFOV, h2vRatio=AUTO_COMPUTE):
		"""Set the vertical FOV and aspect ratio of the window"""
		if _islist(vertFOV):
			_ipcSend(_VIZ_FOV,self.id,0,'',vertFOV[0],vertFOV[1],0.0,0.0)
		else:
			_ipcSend(_VIZ_FOV,self.id,0,'',vertFOV,h2vRatio,0.0,0.0)

	def setNearFarRatio(self,ratio):
		_ipcSend(_VIZ_NEARFARRATIO,self.id,0,'',ratio,0.0,0.0,0.0)

	def clearcolor(self, red,green=1,blue=0,alpha=1):
		"""Set the background color of the window"""
		if _islist(red):
			if len(red) > 3:
				_ipcSend(_VIZ_CLEARCOLOR,self.id,0,'',red[0],red[1],red[2],red[3])
			else:
				_ipcSend(_VIZ_CLEARCOLOR,self.id,0,'',red[0],red[1],red[2],green)
		else:
			_ipcSend(_VIZ_CLEARCOLOR,self.id,0,'',red,green,blue,alpha)

	def setClearMask(self,mask, mode=MASK_SET):
		"""Set the clear mask of the window"""
		_ipcSend(_VIZ_CLEARCOLOR,self.id,1,'',mask,mode,0.0,0.0)

	def setCullMask(self,mask,eye=BOTH_EYE,mode=MASK_SET):
		"""Set cull mask of window"""
		_ipcSend(_VIZ_WINDOWCULLMASK,self.id,mask,'',eye,mode,0.0,0.0)

	def mouse(self, state = ON):
		"""Set mouse navigation of window"""
		_ipcSend(_VIZ_NAVIGATEMOUSE,self.id,state,'',0.0,0.0,0.0,0.0)

	def setPosition(self, left, top=0, mode=WINDOW_NORMALIZED):
		"""Set the position of the window"""
		if _islist(left):
			_ipcSend(_VIZ_WINDOWPOS,self.id,mode,'',left[0],left[1],0.0,0.0)
		else:
			_ipcSend(_VIZ_WINDOWPOS,self.id,mode,'',left,top,0.0,0.0)

	def setSize(self, width, height=0, mode=WINDOW_NORMALIZED):
		"""Set the size of the window"""
		if _islist(width):
			_ipcSend(_VIZ_WINDOWSIZE,self.id,mode,'',width[0],width[1],0.0,0.0)
		else:
			_ipcSend(_VIZ_WINDOWSIZE,self.id,mode,'',width,height,0.0,0.0)

	def setView(self, view):
		"""Set the viewpoint of the window"""
		_ipcSend(_VIZ_WINDOWVIEW,self.id,view.id,'',0.0,0.0,0.0,0.0)

	def setScene(self, scene, eye=BOTH_EYE):
		"""Set the scene to render in the window"""
		_ipcSend(_VIZ_WINDOWSET,self.id,6,'',_sceneID(scene),eye,0.0,0.0)

	def getScene(self, eye=LEFT_EYE):
		"""Get the scene to render in the window"""
		return VizScene._GetObject(_ipcSend(_VIZ_WINDOWGET,_VIEW_SCENE,self.id,'',eye,0.0,0.0,0.0))

#	def setViewLinkable(self, linkable, flag=0, eye=BOTH_EYE):
#		"""Set the linkable for the view source of the window"""
#		if linkable is None:
#			_ipcSend(_VIZ_WINDOWSET,self.id,4,'',-1.0,-1.0,flag,eye)
#		else:
#			linkableType = _getLinkableType(linkable)
#
#			if linkableType < 0:
#				raise TypeError, 'View object is not a linkable type'
#
#			_ipcSend(_VIZ_WINDOWSET,self.id,4,'',linkable.id,linkableType,flag,eye)
#
#	def getViewLinkable(self, eye=BOTH_EYE):
#		"""Get the linkable for the view source of the window"""
#		return None

	def visible(self, state, mode = 0):
		"""Set the visibility of the window"""
		_ipcSend(_VIZ_WINDOWVISIBLE,self.id,state,'',mode,0.0,0.0,0.0)

	def displayToWindow(self,x,y=0,mode=WINDOW_NORMALIZED,eye=BOTH_EYE):
		"""Convert from display coordinates to window coordinates"""
		if _islist(x):
			return _ipcSend(_VIZ_WINDOWCOORDS,self.id,1,'',x[0],x[1],mode,eye)
		return _ipcSend(_VIZ_WINDOWCOORDS,self.id,1,'',x,y,mode,eye)

	def windowToDisplay(self,x,y=0,mode=WINDOW_NORMALIZED):
		"""Convert from window coordinates to display coordinates"""
		if _islist(x):
			return _ipcSend(_VIZ_WINDOWCOORDS,self.id,0,'',x[0],x[1],mode,0.0)
		return _ipcSend(_VIZ_WINDOWCOORDS,self.id,0,'',x,y,mode,0.0)

	def pick(self, info = False, mode = WORLD, pos = (-1,-1), eye = BOTH_EYE, all = False, ignoreBackFace=False, computePath=False, ignoreClipped=False):
		"""Returns the object that the mouse is pointing at"""

		flag = 0
		if not all:
			flag |= _INTERSECT_NEAREST
		if ignoreBackFace:
			flag |= _INTERSECT_IGNORE_BACK_FACE
		if computePath and info:
			flag |= _INTERSECT_COMPUTE_PATH
		if ignoreClipped:
			flag |= _INTERSECT_IGNORE_CLIPPED

		if info:
			return _ipcSend(_VIZ_PICKDETAIL,self.id,mode,'',pos[0],pos[1],eye,flag)
		else:
			return _ipcSend(_VIZ_WINDOWPICK,self.id,mode,'',pos[0],pos[1],eye,flag)

	def pickRect(self, rect, mode = WORLD, eye = BOTH_EYE):
		"""Returns objects that are within the specified screen rectangle (left,bottom,right,top)"""
		_ipcSend(_VIZ_SETMATRIX1,0,0,'',rect[0],rect[1],rect[2],rect[3])
		nodes = _ipcSend(_VIZ_PICKRECT,self.id,mode,'',eye,0.0,0.0,0.0)
		return [ _GetNode(id) for id in nodes ]

#	def pickRectDetail(self, rect, mode = WORLD, eye = BOTH_EYE):
#		"""Returns objects that are within the specified screen rectangle (left,bottom,right,top)"""
#		_ipcSend(_VIZ_SETMATRIX1,0,0,'',rect[0],rect[1],rect[2],rect[3])
#		nodes = _ipcSend(_VIZ_PICKRECT,self.id,mode,'',eye,1.0,0.0,0.0)
#		return [ _GetNode(id) for id in nodes ]

	def screenToWorld(self,x,y=0,eye=BOTH_EYE,mode=WINDOW_NORMALIZED):
		"""Takes the given 2D coordinates and returns the line that
	passes through it in 3D coordinates, [x1,y1,z1,x2,y2,z2]"""
		if _islist(x):
			return Line(_ipcSend(_VIZ_SCREENTOWORLD,self.id,eye,'',x[0],x[1],0.0,mode))
		return Line(_ipcSend(_VIZ_SCREENTOWORLD,self.id,eye,'',x,y,0.0,mode))

	def worldToScreen(self,x,y=0,z=0,eye=BOTH_EYE,mode=WINDOW_NORMALIZED):
		"""Takes the given 3D coordinates and returns the 2D screen coordinates"""
		if _islist(x):
			return _ipcSend(_VIZ_WORLDTOSCREEN,self.id,eye,'',x[0],x[1],x[2],mode)
		return _ipcSend(_VIZ_WORLDTOSCREEN,self.id,eye,'',x,y,z,mode)

	def isCulled(self,node,name='',eye=BOTH_EYE):
		"""Returns whether an object is culled by the view frustum"""
		return _ipcSend(_VIZ_ISCHILDCULLED,self.id,node.id,name,eye,0.0,0.0,0.0)

	def ipd(self, meters):
		"""Set the distance between the eyes for stereo viewing"""
		_ipcSend(_VIZ_IPD,self.id,0,'',meters,0.0,0.0,0.0)

	def ipdVector(self, v, mode=PRE_MULT):
		"""Set the left to right vector to use for separating viewpoint ipd"""
		if v is None:
			_ipcSend(_VIZ_WINDOWSET,self.id,3,'',0.0,0.0,0.0,0.0)
		else:
			_ipcSend(_VIZ_WINDOWSET,self.id,2,'',v[0],v[1],v[2],mode)

	def stereo(self, mode):
		"""Change the stereo mode"""
		_ipcSend(_VIZ_STEREOMODE,self.id,mode,'',0.0,0.0,0.0,0.0)

	def setStereoSwap(self, mode):
		"""Set whether left/right eyes should be swapped during stereo rendering"""
		_ipcSend(_VIZ_WINDOWSET,self.id,5,'',mode,0.0,0.0,0.0)

	def screenDistance(self, meters):
		"""Set the distance between the user and the monitor, for stereo viewing"""
		_ipcSend(_VIZ_SCREENDIST,self.id,0,'',meters,0.0,0.0,0.0)

	def fusionDistance(self,value,mode=DISTANCE):
		"""Set the fusion distance for stereo viewing"""
		_ipcSend(_VIZ_SETFUSEDIST,self.id,mode,'',value,0.0,0.0,0.0)

	def stereoOverlap(self, overlap):
		"""Set the overlap percentage for stereo"""
		_ipcSend(_VIZ_STEREOOVERLAP,self.id,0,'',overlap,0.0,0.0,0.0)

	def setViewOffset(self, matrix, eye=BOTH_EYE, mode=PRE_MULT):
		"""Set the view offset for a window"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', matrix[0], matrix[1], matrix[2], matrix[3])
		_ipcSend(_VIZ_SETMATRIX2, 0, 0, '', matrix[4], matrix[5], matrix[6], matrix[7])
		_ipcSend(_VIZ_SETMATRIX3, 0, 0, '', matrix[8], matrix[9], matrix[10], matrix[11])
		_ipcSend(_VIZ_SETMATRIX4, 0, 0, '', matrix[12], matrix[13], matrix[14], matrix[15])
		_ipcSend(_VIZ_VIEWOFFSET,self.id,eye,'',mode,0.0,0.0,0.0)

	@DeprecateObject
	def setOrthoOffset(self, offset):
		"""Set the pixel offset for ortho graphic nodes in stereo"""
		_ipcSend(_VIZ_WINDOWSET,self.id,1,'',offset,0.0,0.0,0.0)

	def setCropRect(self, rect, mode=WORLD, eye=BOTH_EYE):
		"""Set the (left,bottom,right,top) crop rectangle for the window projection matrix"""
		if rect is None:
			rect = (0.0,0.0,1.0,1.0)
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '',rect[0],rect[1],rect[2],rect[3])
		_ipcSend(_VIZ_WINSETFRUSTUM,self.id,3,'',mode,eye,0.0,0.0)

	def setDefaultGUICanvas(self, canvas):
		"""Set default GUI canvas for window"""
		if canvas is None:
			id = -1
		else:
			id = canvas.id
		_ipcSend(_VIZ_WINDOWSET,self.id,7,'',id,0.0,0.0,0.0)

	def getDefaultGUICanvas(self):
		"""Get default GUI canvas for window"""
		return _ipcSend(_VIZ_WINDOWGET,130,self.id,'',0.0,0.0,0.0,0.0)

	def setTagRender(self, tags, mode):
		"""Set render mode for tag"""
		if _islist(tags):
			tags = _NAME_DELIMETER.join(tags)
		_ipcSend(_VIZ_SETTAGRENDER, self.id, mode, tags, 0.0, 0.0, 0.0, 1.0)

	def getTagRender(self, tag):
		"""Get render mode for tag"""
		return _ipcSend(_VIZ_WINDOWGET,133,self.id,tag,0.0,0.0,0.0,0.0)

MainWindow = VizWindow(0)
LeftTop			= MainWindow.LeftTop
LeftCenter		= MainWindow.LeftCenter
LeftBottom		= MainWindow.LeftBottom
RightTop		= MainWindow.RightTop
RightCenter		= MainWindow.RightCenter
RightBottom		= MainWindow.RightBottom
CenterTop		= MainWindow.CenterTop
CenterCenter	= MainWindow.CenterCenter
CenterBottom	= MainWindow.CenterBottom
WindowSize		= MainWindow.WindowSize

# Sound3D commands
_SOUND3D_VELOCITY	= 12
_SOUND3D_SETTIME	= 13
_SOUND3D_VOLUME		= 14

#DX specific Sound3D commands
_SOUND3D_DX_CONEANGLES	= 0
_SOUND3D_DX_CONEVOLUME	= 1
_SOUND3D_DX_MINMAXDIST	= 2

class VizSound3D(VizObject):
	"""VizSound3D object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_SOUND_3D

	def __init__(self, id):
		VizObject.__init__(self, id)

	def remove(self):
		"""Remove the 3d sound object"""
		_ipcSend(_VIZ_SOUND3DREMOVE,self.id,0,'',0.0,0.0,0.0,0.0)

	def play(self,loop=0):
		"""Play the 3d sound"""
		if loop:
			_ipcSend(_VIZ_PERFORMSOUND3D,self.id,LOOP,'',0.0,0.0,0.0,0.0)
		else:
			_ipcSend(_VIZ_PERFORMSOUND3D,self.id,PLAY,'',0.0,0.0,0.0,0.0)

	def pause(self):
		"""Pause the 3d sound"""
		_ipcSend(_VIZ_PERFORMSOUND3D,self.id,PAUSE,'',0.0,0.0,0.0,0.0)

	def stop(self):
		"""Stop the 3d sound"""
		_ipcSend(_VIZ_PERFORMSOUND3D,self.id,STOP,'',0.0,0.0,0.0,0.0)

	def velocity(self,vx,vy=0,vz=0):
		"""Set the velocity of the 3d sound"""
		if _islist(vx):
			_ipcSend(_VIZ_PERFORMSOUND3D,self.id,_SOUND3D_VELOCITY,'',vx[0],vx[1],vx[2],0.0)
		else:
			_ipcSend(_VIZ_PERFORMSOUND3D,self.id,_SOUND3D_VELOCITY,'',vx,vy,vz,0.0)

	def command(self,command,mesg='',x=0.0,y=0.0,z=0.0,w=0.0):
		"""Send a command to the 3d sound object"""
		_ipcSend(_VIZ_COMMANDSOUND3D,self.id,command,mesg,x,y,z,w)

	def coneangle(self,inner,outer):
		"""Set the inner and outer angle of the sound cone"""
		_ipcSend(_VIZ_COMMANDSOUND3D,self.id,_SOUND3D_DX_CONEANGLES,'',inner,outer,0.0,0.0)

	def conevolume(self,volume):
		"""Set the volume of the sound outside its cone"""
		_ipcSend(_VIZ_COMMANDSOUND3D,self.id,_SOUND3D_DX_CONEVOLUME,'',volume,0.0,0.0,0.0)

	def minmax(self,minDistance,maxDistance):
		"""Set the min and max distances of the sound"""
		_ipcSend(_VIZ_COMMANDSOUND3D,self.id,_SOUND3D_DX_MINMAXDIST,'',minDistance,maxDistance,0.0,0.0)

	def setTime(self, time):
		"""Set the time of the sound in seconds"""
		_ipcSend(_VIZ_PERFORMSOUND3D,self.id,_SOUND3D_SETTIME,'',time,0.0,0.0,0.0)

	def getTime(self):
		"""Get the time of the sound in seconds"""
		return _ipcSend(_VIZ_SOUND3DGET,self.id,1,'',0.0,0.0,0.0,0.0)

	def getDuration(self):
		"""Get the duration of the sound in seconds"""
		return _ipcSend(_VIZ_SOUND3DGET,self.id,2,'',0.0,0.0,0.0,0.0)

	def getState(self):
		"""Return the playback state of the sound"""
		return _ipcSend(_VIZ_SOUND3DGET,self.id,3,'',0.0,0.0,0.0,0.0)

	def getFilename(self):
		"""Return the filename of the sound"""
		return _ipcSend(_VIZ_SOUND3DGET,self.id,4,'',0.0,0.0,0.0,0.0)

	def volume(self,volume):
		"""Set the volume of the sound"""
		_ipcSend(_VIZ_PERFORMSOUND3D,self.id,_SOUND3D_VOLUME,'',volume,0.0,0.0,0.0)

class VizAudio(VizObject):
	"""VizAudio object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_MEDIA

	def __init__(self, id, play=None, loop=None, volume=None, **kw):
		VizObject.__init__(self, id)

		if self.valid():
			if loop is not None:
				self.loop(loop)
			if volume is not None:
				self.volume(volume)
			if play:
				self.play()

	def remove(self):
		"""Delete the media object"""
		_ipcSend(_VIZ_DELMEDIA,self.id,0,'',0.0,0.0,0.0,0.0)

	def play(self):
		"""Play the media"""
		_ipcSend(_VIZ_MEDIAPLAY,self.id,0,'',0.0,0.0,0.0,0.0)

	def pause(self):
		"""Pause the media"""
		_ipcSend(_VIZ_MEDIAPAUSE,self.id,0,'',0.0,0.0,0.0,0.0)

	def stop(self):
		"""Stop the media"""
		_ipcSend(_VIZ_MEDIASTOP,self.id,0,'',0.0,0.0,0.0,0.0)

	def volume(self, volume):
		"""Set the volume of the media"""
		_ipcSend(_VIZ_MEDIAVOLUME,self.id,0,'',volume,0.0,0.0,0.0)

	def setBalance(self, balance):
		"""Set the audio balance of the media"""
		_ipcSend(_VIZ_MEDIABALANCE,self.id,0,'',balance,0.0,0.0,0.0)

	def setTime(self, time):
		"""Jump to the given time in the media"""
		_ipcSend(_VIZ_MEDIAPOS,self.id,0,'',time,0.0,0.0,0.0)

	def setFrame(self,frame):
		"""Jump to the given video frame"""
		_ipcSend(_VIZ_MEDIAPOS,self.id,1,'',frame,0.0,0.0,0.0)

	def setRate(self, rate):
		"""Set the playback rate"""
		_ipcSend(_VIZ_MEDIARATE,self.id,0,'',rate,0.0,0.0,0.0)

	def loop(self, loop = ON):
		"""Turn looping ON or OFF"""
		_ipcSend(_VIZ_MEDIALOOP,self.id,loop,'',0.0,0.0,0.0,0.0)

	def stoptime(self, time):
		"""Set the time in the media that it will stop at"""
		_ipcSend(_VIZ_MEDIASTOPTIME,self.id,0,'',time,0.0,0.0,0.0)

	def getDuration(self):
		"""Get the duration of the media"""
		return _ipcSend(_VIZ_MEDIAGET,LENGTH,self.id,'',0.0,0.0,0.0,0.0)

	def getTime(self):
		"""Get the current position of the media"""
		return _ipcSend(_VIZ_MEDIAGET,POSITION,self.id,'',0.0,0.0,0.0,0.0)

	def getFrame(self):
		"""Get the current frame of the media"""
		return _ipcSend(_VIZ_MEDIAGET,_VID_FRAME,self.id,'',0.0,0.0,0.0,0.0)

	def getFrameCount(self):
		"""Get the number of frames of the media"""
		return _ipcSend(_VIZ_MEDIAGET,_VID_FRAME_COUNT,self.id,'',0.0,0.0,0.0,0.0)

	def getState(self):
		"""Get the current state of the media"""
		return _ipcSend(_VIZ_MEDIAGET,_MEDIA_STATE,self.id,'',0.0,0.0,0.0,0.0)

	def getFilename(self):
		"""Get the filename of the media object"""
		return _ipcSend(_VIZ_MEDIAGET,FILENAME,self.id,'',0.0,0.0,0.0,0.0)

class VizSoundMixer(VizLinkable):
	"""VizSoundMixer object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_SOUND_MIXER
	_VizLinkableType = _VIZ_SOUND_MIXER_LINKABLE

	def __init__(self, id):
		VizLinkable.__init__(self, id)

	def remove(self):
		"""Remove the mixer and all child mixers"""
		_ipcSend(_VIZ_MIXERSET, 2, self.id, '',0.0,0.0,0.0,0.0)

	def play(self, filename, flags=PLAY):
		"""Play a sound on the mixer"""
		_ipcSend(_VIZ_MIXERSET, 3, self.id, filename, flags, 0.0, 0.0, 0.0)

	def stop(self):
		"""Stop all sounds on the mixer"""
		_ipcSend(_VIZ_MIXERSET, 4, self.id, '',0.0,0.0,0.0,0.0)

	def stopLoop(self):
		"""Stop looping all sounds once they have reached the end of the next loop"""
		_ipcSend(_VIZ_MIXERSET, 10, self.id, '',0.0,0.0,0.0,0.0)

	def setPaused(self, mode):
		"""Set paused mode of sound mixer"""
		_ipcSend(_VIZ_MIXERSET, 5, self.id, '',mode,0.0,0.0,0.0)

	def getPaused(self):
		"""Return whether the sound mixer is paused"""
		return _ipcSend(_VIZ_MIXERGET, 5, self.id, '',0.0,0.0,0.0,0.0)

	def setVolume(self, value):
		"""Set volume of the sound mixer"""
		_ipcSend(_VIZ_MIXERSET, 6, self.id, '',value,0.0,0.0,0.0)

	def getVolume(self):
		"""Get volume of the sound mixer"""
		return _ipcSend(_VIZ_MIXERGET, 6, self.id, '',0.0,0.0,0.0,0.0)

	def getChannelCount(self):
		"""Get number of channels output by the sound mixer"""
		return _ipcSend(_VIZ_MIXERGET, 11, self.id, '',0.0,0.0,0.0,0.0)

	def getChannelMask(self):
		"""Get mask of channels output by the sound mixer"""
		return _ipcSend(_VIZ_MIXERGET, 10, self.id, '',0.0,0.0,0.0,0.0)

	def setChannelVolume(self, mask, value):
		"""Set per channel volume of the sound mixer"""
		_ipcSend(_VIZ_MIXERSET, 9, self.id, '',mask,value,0.0,0.0)

	def getChannelVolume(self, mask):
		"""Get per channel volume of the sound mixer"""
		return _ipcSend(_VIZ_MIXERGET, 9, self.id, '',mask,0.0,0.0,0.0)

	def setPitch(self, value):
		"""Set the pitch of the sound mixer"""
		_ipcSend(_VIZ_MIXERSET, 7, self.id, '',value,0.0,0.0,0.0)

	def getPitch(self):
		"""Get the pitch of the sound mixer"""
		return _ipcSend(_VIZ_MIXERGET, 7, self.id, '',0.0,0.0,0.0,0.0)

	def setFilter(self, filter):
		"""Set the audio filter parameters
		@arg filter AudioFilter()"""
		_ipcSend(_VIZ_MIXERSET, 8, self.id, '', filter.mode, filter.frequency, filter.Q, 0.0)

	def getFilter(self):
		"""Get the audio filter parameters"""
		return AudioFilter(*_ipcSend(_VIZ_MIXERGET, 8, self.id, '',0.0,0.0,0.0,0.0))

	def setMode(self, mode, value):
		"""Set a mode on the sound mixer"""
		if _islist(mode):
			for m in mode:
				_ipcSend(_VIZ_MIXERSET, 12, self.id, '', m, value, 0.0, 0.0)
		else:
			_ipcSend(_VIZ_MIXERSET, 12, self.id, '', mode, value, 0.0, 0.0)

	def getMode(self, mode):
		"""Get a mode value from the sound mixer"""
		return _ipcSend(_VIZ_MIXERGET, 12, self.id, '', mode, 0.0, 0.0, 0.0)

	def enable(self, mode):
		"""Enable a mode on the sound mixer"""
		self.setMode(mode, 1)

	def disable(self, mode):
		"""Disable a mode on the sound mixer"""
		self.setMode(mode, 0)

	def syncState(self):
		self.enable(-43)

class VizTexture(VizObject, VizEventTarget):
	"""VizTexture object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_TEXTURE

	def __init__(self,id,texType=_VIZ_TEX_TEX,base=None,filter=None,wrap=None,minFilter=None,magFilter=None,wrapS=None,wrapT=None,wrapR=None,compression=None,anisotropy=None,autoScale=None,resizeNPOT=None,borderColor=None,shadow=None,**kw):
		VizObject.__init__(self,id,base)
		self._textype = texType

		if filter is not None:
			self.filter(MIN_FILTER,filter)
			self.filter(MAG_FILTER,filter)
		if wrap is not None:
			self.wrap(WRAP_S,wrap)
			self.wrap(WRAP_T,wrap)
			self.wrap(WRAP_R,wrap)
		if minFilter is not None:
			self.filter(MIN_FILTER,minFilter)
		if magFilter is not None:
			self.filter(MAG_FILTER,magFilter)
		if wrapS is not None:
			self.wrap(WRAP_S,wrapS)
		if wrapT is not None:
			self.wrap(WRAP_T,wrapT)
		if wrapR is not None:
			self.wrap(WRAP_R,wrapR)
		if compression is not None:
			self.compression(compression)
		if anisotropy is not None:
			self.anisotropy(anisotropy)
		if autoScale is not None:
			self.autoScale(autoScale)
		if resizeNPOT is not None:
			self.setMode(TEXTURE_RESIZE_NPOT,resizeNPOT)
		if borderColor is not None:
			self.setBorderColor(borderColor)
		if shadow is not None:
			self.shadow(shadow)

	def remove(self):
		"""Delete the texture"""
		_ipcSend(_VIZ_TEXREMOVE,self.id,self._textype,'',0.0,0.0,0.0,0.0)

	def copy(self, **kw):
		"""Return a copy of the texture
		@return VizTexture()"""
		return self.__class__(_ipcSend(_VIZ_ADDTEXTURE, self.id, self._textype, '', 0.0, 0.0, 0.0, 1.0), **kw)

	def unapply(self, unit=AUTO_COMPUTE):
		"""Unapply texture from all objects"""
		_ipcSend(_VIZ_TEXTURESET,self.id,self._textype,'',5,unit,0.0,0.0)

	def load(self, filename, face = POSITIVE_X, flags=0):
		"""Load an image file into the texture object"""
		return _ipcSend(_VIZ_LOADTEXTURE,self.id,face,filename,self._textype,flags,0.0,0.0)

	def loadBuffer(self, filename, buffer, face = POSITIVE_X, flags = 0):
		"""Load an image buffer into the texture object"""

		#Get buffer
		buffer = _getBuffer(filename,buffer)

		_ipcSend(_VIZ_SETSTRING,0,0,filename,0.0,0.0,0.0,0.0)
		return bool(_ipcSend(_VIZ_ADDTEXBUFFER,self.id,face,buffer,self._textype,flags,0.0,1.0))

	def setImageData(self, data, size, format = TEX_RGB, face = POSITIVE_X):
		"""Set the raw image data of the texture"""
		s = list(size) + [1,1] #Ensures size is at least 3 elements large
		return _ipcSend(_VIZ_TEXSETDATA,self.id,format,data,s[0],s[1],s[2],face)

	def setPixelFormat(self, format):
		"""Set the pixel format for render textures"""
		_ipcSend(_VIZ_TEXTURESET,self.id,self._textype,'',7.0,format,0.0,0.0)

	def filter(self,parameter,mode):
		"""Set the filter mode of the texture"""
		_ipcSend(_VIZ_TEXFILTERMODE,self.id,parameter,'',mode,self._textype,0.0,0.0)

	def wrap(self,parameter,mode):
		"""Set the wrap mode of the texture"""
		_ipcSend(_VIZ_TEXWRAPMODE,self.id,parameter,'',mode,self._textype,0.0,0.0)

	def compression(self,mode):
		"""Set the compression mode of the texture"""
		_ipcSend(_VIZ_TEXCOMPRESS,self.id,mode,'',self._textype,0.0,0.0,0.0)

	def anisotropy(self,value):
		"""Set the level of anisotropy for the texture"""
		_ipcSend(_VIZ_TEXANISOTROPY,self.id,self._textype,'',value,0.0,0.0,0.0)

	def autoScale(self,value,matrix=None):
		"""Set whether the texture will automatically scale texture coordinates when applied"""
		if matrix is None:
			_ipcSend(_VIZ_TEXTURESET,self.id,self._textype,'',0.0,value,0.0,0.0)
		else:
			_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', matrix[0], matrix[1], matrix[2], matrix[3])
			_ipcSend(_VIZ_SETMATRIX2, 0, 0, '', matrix[4], matrix[5], matrix[6], matrix[7])
			_ipcSend(_VIZ_SETMATRIX3, 0, 0, '', matrix[8], matrix[9], matrix[10], matrix[11])
			_ipcSend(_VIZ_SETMATRIX4, 0, 0, '', matrix[12], matrix[13], matrix[14], matrix[15])
			_ipcSend(_VIZ_TEXTURESET,self.id,self._textype,'',4.0,value,0.0,0.0)

	def setMode(self, mode, value):
		"""Set a mode on the texture"""
		if _islist(mode):
			for m in mode:
				_ipcSend(_VIZ_TEXTURESET,self.id,self._textype,'',6.0,m,value,0.0)
		else:
			_ipcSend(_VIZ_TEXTURESET,self.id,self._textype,'',6.0,mode,value,0.0)

	def getMode(self, mode):
		"""Get a mode value from the texture"""
		return _ipcSend(_VIZ_TEXTUREGET,119,self.id,'',self._textype,mode,0.0,0.0)

	def enable(self, mode):
		"""Enable a mode on the texture"""
		self.setMode(mode,1)

	def disable(self, mode):
		"""Disable a mode on the texture"""
		self.setMode(mode,0)

	@DeprecateObject
	def resizeNPOT(self,value):
		"""Set whether the texture will resize non-power-of-two textures"""
		self.setMode(TEXTURE_RESIZE_NPOT,value)

	def setBorderColor(self,color):
		"""Set the border color of the texture"""
		if len(color) < 4:
			_ipcSend(_VIZ_TEXBORDERCOLOR,self.id,self._textype,'',color[0],color[1],color[2],1.0)
		else:
			_ipcSend(_VIZ_TEXBORDERCOLOR,self.id,self._textype,'',color[0],color[1],color[2],color[3])

	def modify(self, modifier, command = 0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0):
		"""Send the texture to the given modifier"""
		if isinstance(modifier,VizModifier):
			_ipcSend(_VIZ_MODIFYPARAMS,modifier.id,command,mesg,x,y,z,w)
			_ipcSend(_VIZ_MODIFYTEXTURE,modifier.id,self.id,'',self._textype,0.0,0.0,0.0)

	def hint(self, flag):
		"""Apply hint flags to the texture"""
		_ipcSend(_VIZ_TEXTURESET,self.id,self._textype,'',2,flag,0.0,0.0)

	@DeprecateObject
	def shadow(self, value=True):
		"""Set shadow texture"""
		self.setMode(TEXTURE_SHADOW,value)

	def getSize(self):
		"""Get size of texture"""
		return _ipcSend(_VIZ_TEXTUREGET,SCALE,self.id,'',self._textype,0.0,0.0,0.0)

	def getMinFilter(self):
		"""Get the minification filter mode"""
		return _ipcSend(_VIZ_TEXTUREGET,FILTER_MODE,self.id,'',self._textype,MIN_FILTER,0.0,0.0)

	def getMagFilter(self):
		"""Get the magnification filter mode"""
		return _ipcSend(_VIZ_TEXTUREGET,FILTER_MODE,self.id,'',self._textype,MAG_FILTER,0.0,0.0)

	def getWrap(self,param):
		"""Get the wrap mode"""
		return _ipcSend(_VIZ_TEXTUREGET,WRAP_MODE,self.id,'',self._textype,param,0.0,0.0)

	def getCompression(self):
		"""Get the compression mode"""
		return _ipcSend(_VIZ_TEXTUREGET,COMPRESSION,self.id,'',self._textype,0.0,0.0,0.0)

	def getAnisotropy(self):
		"""Get the anisotropy value"""
		return _ipcSend(_VIZ_TEXTUREGET,ANISOTROPY,self.id,'',self._textype,0.0,0.0,0.0)

	def getType(self):
		"""Get the texture type"""
		return _ipcSend(_VIZ_TEXTUREGET,TEXTURE_TYPE,self.id,'',self._textype,0.0,0.0,0.0)

	def getFilename(self):
		"""Get filename of texture"""
		return _ipcSend(_VIZ_TEXTUREGET,FILENAME,self.id,'',self._textype,0.0,0.0,0.0)

	def getImageData(self,face=POSITIVE_X):
		"""Get texture image data"""
		return _ipcSend(_VIZ_TEXTUREGET,_TEXTURE_DATA,self.id,'',self._textype,face,0.0,0.0)

	def getPixelSize(self):
		"""Get the size of each pixel, in bytes"""
		return _ipcSend(_VIZ_TEXTUREGET,_PIXEL_SIZE,self.id,'',self._textype,0.0,0.0,0.0)

	def getPixelFormat(self):
		"""Get the pixel format of the texture"""
		return _ipcSend(_VIZ_TEXTUREGET,_PIXEL_FORMAT,self.id,'',self._textype,0.0,0.0,0.0)

	def getHandle(self):
		"""Get the underlying graphics handle of the texture"""
		return _ipcSend(_VIZ_TEXTUREGET,_WINDOW_HANDLE,self.id,'',self._textype,0.0,0.0,0.0)

	def save(self, filename, face = POSITIVE_X):
		"""Save texture to file"""
		return _ipcSend(_VIZ_SAVECHILD,self.id,1,filename,self._textype,face,0.0,0.0)

	def saveToBuffer(self, filename, face = POSITIVE_X, dataType = GL_UNSIGNED_BYTE):
		"""Save texture to buffer"""
		return _ipcSend(_VIZ_SAVECHILD,self.id,2,filename,self._textype,face,dataType,0.0)

	def getAsyncStatus(self):
		"""Get status of async loaded texture"""
		return _ipcSend(_VIZ_TEXTUREGET,120,self.id,'',self._textype,0.0,0.0,0.0)

	def setBorderRect(self, rect):
		"""Set (left, bottom, right, top) border rectangle in normalized units"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', rect[0], rect[1], rect[2], rect[3])
		_ipcSend(_VIZ_TEXTURESET,self.id,self._textype,'',8,0.0,0.0,0.0)

	def getBorderRect(self):
		"""Get (left, bottom, right, top) border rectangle in normalized units"""
		return _ipcSend(_VIZ_TEXTUREGET,115,self.id,'',self._textype,0.0,0.0,0.0)

	def getAnimationDuration(self):
		return _ipcSend(_VIZ_TEXTUREGET, _ANIMATION_DURATION, self.id, '', 0.0, 0.0, 0.0, 0.0)

	def getAnimationFrameCount(self):
		return _ipcSend(_VIZ_TEXTUREGET, 138, self.id, '', 0.0, 0.0, 0.0, 0.0)

	def getAnimationTime(self):
		return _ipcSend(_VIZ_TEXTUREGET, _ANIMATION_TIME, self.id, '', 0.0, 0.0, 0.0, 0.0)

	def setAnimationTime(self, time, flags=0):
		_ipcSend(_VIZ_TEXTURESET, self.id, 0, '', 9, time, flags, 0.0)

	def getAnimationFrame(self):
		return _ipcSend(_VIZ_TEXTUREGET, 137, self.id, '', 0.0, 0.0, 0.0, 0.0)

	def setAnimationFrame(self, frame, flags=0):
		_ipcSend(_VIZ_TEXTURESET, self.id, 0, '', 10, frame, flags, 0.0)

	def getAnimationState(self):
		return _ipcSend(_VIZ_TEXTUREGET, 136, self.id, '', 0.0, 0.0, 0.0, 0.0)

	def setAnimationState(self, state):
		_ipcSend(_VIZ_TEXTURESET, self.id, 0, '', 11, state, 0.0, 0.0)

	def getAnimationLoopMode(self):
		return _ipcSend(_VIZ_TEXTUREGET, 135, self.id, '', 0.0, 0.0, 0.0, 0.0)

	def setAnimationLoopMode(self, loopMode):
		_ipcSend(_VIZ_TEXTURESET, self.id, 0, '', 12, loopMode, 0.0, 0.0)

	def getAnimationSpeed(self):
		return _ipcSend(_VIZ_TEXTUREGET, _ANIMATION_SPEED, self.id, '', 0.0, 0.0, 0.0, 0.0)

	def setAnimationSpeed(self, speed):
		_ipcSend(_VIZ_TEXTURESET, self.id, 0, '', 13, speed, 0.0, 0.0)

	def getVolume(self):
		return _ipcSend(_VIZ_TEXTUREGET, 139, self.id, '', 0.0, 0.0, 0.0, 0.0)

	def setVolume(self, volume):
		_ipcSend(_VIZ_TEXTURESET, self.id, 0, '', 14, volume, 0.0, 0.0)

class VizImageGen(VizTexture):
	"""VizImageGen object"""
	def __init__(self,id):
		VizTexture.__init__(self,id,_VIZ_TEX_TEX)

	def command(self,command,mesg='',x=0.0,y=0.0,z=0.0,w=0.0):
		"""Send a command to the Image Generator"""
		_ipcSend(_VIZ_COMMANDIMGGEN,self.id,command,mesg,x,y,z,w)

	def get(self,*args):
		"""Retrieve data from the Image Generator"""
		if args:
			return VizTexture.get(self,*args)
		return _ipcSend(_VIZ_GETIMAGEGEN,self.id,0,'',0.0,0.0,0.0,0.0)

class VizVideoCapture(VizImageGen):

	def refresh(self):
		"""Refresh the image"""
		self.command(0)

	def save(self,filename):
		"""Save the current image to file"""
		self.command(1,filename)

	def live(self,mode):
		"""Set whether the image will update continuously"""
		if mode:
			self.command(3)
		else:
			self.command(2)

	def delay(self,frames):
		"""Set the number of frames to delay the image"""
		self.command(4,'',frames)

	def autogain(self,mode):
		"""Set automatic input gain on/off"""
		self.command(5,'',mode)

	def gain(self,val):
		"""Set the input gain"""
		self.command(6,'',val)

	def saturation(self,val):
		"""Set the saturation level"""
		self.command(7,'',val)

	def contrast(self,val):
		"""Set the contrast level"""
		self.command(8,'',val)

	def hue(self,val):
		"""Set the hue"""
		self.command(9,'',val)

	def brightness(self,val):
		"""Set the brightness"""
		self.command(10,'',val)

	def gamma(self,val):
		"""Set the gamma"""
		self.command(11,'',val)

	def exposure(self,val):
		"""Set the exposure"""
		self.command(12,'',val)

	def shutterspeed(self,val):
		"""Set the shutterspeed"""
		self.command(13,'',val)

	def framerate(self,val):
		"""Set the framerate"""
		self.command(14,'',val)

	def flushbuffer(self):
		"""Flush contents of delay buffer to files"""
		self.command(20)

upgradeImageGen('videocapture.dlt',VizVideoCapture)

class VizVideoTexture(VizAudio,VizTexture):
	"""VizVideoTexture object"""
	def __init__(self,id,**kw):
		VizAudio.__init__(self,id,**kw)
		VizTexture.__init__(self,id,_VIZ_VID_TEX,**kw)

	def remove(self):
		"""Delete the media object"""
		VizAudio.remove(self)

	def setLiveUpdate(self, mode):
		"""Set whether the video texture image is updated in real-time"""
		_ipcSend(_VIZ_MEDIASET,self.id,1,'',mode,0.0,0.0,0.0)

	def updateImage(self):
		"""Manually update the video texture image to the most recent frame"""
		_ipcSend(_VIZ_MEDIASET,self.id,2,'',0.0,0.0,0.0,0.0)

class VizTransformNodeLinkable(VizActor, VizCustomLinkable):
	"""Handle to a sub-transform node"""
	def __init__(self,id):
		VizActor.__init__(self)
		VizCustomLinkable.__init__(self,id)

class VizNode(VizObject, VizActor, VizEventTarget):
	"""VizNode object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_NODE
	_VizLinkableType = _VIZ_NODE_LINKABLE

	def __init__(self,id,pos=None,quat=None,euler=None,axisAngle=None,scale=None,color=None,alpha=None,texture=None,disable=None,enable=None,align=None,encoding=None,font=None,fontSize=None,opMode=None):
		VizActor.__init__(self)
		VizObject.__init__(self, id)

		if self.valid():
			if opMode is not None:
				self.setOpMode(opMode)
			if pos is not None:
				self.setPosition(pos)
			if quat is not None:
				self.setQuat(quat)
			if euler is not None:
				self.setEuler(euler)
			if axisAngle is not None:
				self.setAxisAngle(axisAngle)
			if scale is not None:
				self.setScale(scale)
			if color is not None:
				self.color(color)
			if alpha is not None:
				self.alpha(alpha)
			if texture is not None:
				self.texture(texture)
			if align is not None:
				self.alignment(align)
			if enable is not None:
				self.enable(enable)
			if disable is not None:
				self.disable(disable)
			if encoding is not None:
				self.setEncoding(encoding)
			if font is not None:
				self.font(font)
			if fontSize is not None:
				self.fontSize(fontSize)

	def reset(self):
		"""Reset the node"""
		_ipcSend(_VIZ_RESET,self.id,-1,'',0.0,0.0,0.0,0.0)

	def remove(self,children=True):
		"""Permanently remove the node from the scene"""
		_ipcSend(_VIZ_REMOVECHILD,self.id,children,'',0.0,0.0,0.0,0.0)

	def setParent(self, parent, scene = MainScene, node=''):
		"""Change the parent of the node"""
		_ipcSend(_VIZ_SETPARENT,self.id,int(parent),node,_sceneID(scene),0.0,0.0,0.0)

	def addParent(self, parent, scene = MainScene, node=''):
		"""Add another parent to the node"""
		_ipcSend(_VIZ_DUPLICATECHILD,self.id,int(parent),node,_sceneID(scene),0.0,0.0,0.0)

	def removeParent(self, parent, scene = MainScene):
		"""Remove node from specified parent"""
		_ipcSend(_VIZ_SETPARENT,self.id,int(parent),'',_sceneID(scene),0.0,0.0,1.0)

	def clearParents(self, node=''):
		"""Remove node from all parents"""
		_ipcSend(_VIZ_SETPARENT,self.id,0,node,0.0,0.0,0.0,2.0)

	def clearChildren(self, node=''):
		"""Remove all children from node"""
		_ipcSend(_VIZ_SETPARENT,self.id,0,node,0.0,0.0,0.0,3.0)

	def getPosition(self, mode = ABS_PARENT):
		"""Get position of node"""
		return _ipcSend(_VIZ_CHILDGET,POSITION,self.id,'',mode,0.0,0.0,0.0)

	def getCenter(self, mode = ABS_PARENT):
		"""Get position of node"""
		return _ipcSend(_VIZ_CHILDGET,CENTER,self.id,'',mode,0.0,0.0,0.0)

	def getScale(self, mode = ABS_PARENT):
		"""Get scale of node"""
		return _ipcSend(_VIZ_CHILDGET,SCALE,self.id,'',mode,0.0,0.0,0.0)

	def getEuler(self, mode = ABS_PARENT):
		"""Get euler angle of node"""
		return _ipcSend(_VIZ_CHILDGET,EULER,self.id,'',mode,0.0,0.0,0.0)

	def getAxisAngle(self, mode = ABS_PARENT):
		"""Get axis angle of node"""
		return _ipcSend(_VIZ_CHILDGET,AXISANGLE,self.id,'',mode,0.0,0.0,0.0)

	def getQuat(self, mode = ABS_PARENT):
		"""Get quaternion of node"""
		return _ipcSend(_VIZ_CHILDGET,QUAT,self.id,'',mode,0.0,0.0,0.0)

	def getMatrix(self, mode = ABS_PARENT, node=''):
		"""Get matrix of node"""
		return Transform(_ipcSend(_VIZ_CHILDGET,MATRIX,self.id,node,mode,0.0,0.0,0.0))

	def getLineForward(self, mode=ABS_PARENT, length=1.0):
		"""Return Line object starting at linkable position and ending at specified length along forward vector"""
		return Line(_ipcSend(_VIZ_LINKABLE_GET,LOOK,self.id,'',self._VizLinkableType,mode,length,0.0))

	def getBoundingBox(self, mode = ABS_PARENT, node='', op=OP_DEFAULT, flags=0):
		"""Get bounding box of node"""
		return BoundingBox(_ipcSend(_VIZ_CHILDGET,BOUNDING_BOX,self.id,node,mode,op,flags,0.0))

	def getBoundingSphere(self, mode = ABS_PARENT, node='', op=OP_DEFAULT, flags=0):
		"""Get bounding sphere of node"""
		return BoundingSphere(_ipcSend(_VIZ_CHILDGET,BOUNDING_SPHERE,self.id,node,mode,op,flags,0.0))

	def getColor(self, node='',op=OP_DEFAULT,mode=COLOR_DIFFUSE):
		"""Get diffuse color"""
		return _ipcSend(_VIZ_CHILDGET,COLOR,self.id,node,mode,op,0.0,0.0)

	def getSpecular(self, node='',op=OP_DEFAULT):
		"""Get specular color"""
		return _ipcSend(_VIZ_CHILDGET,COLOR,self.id,node,1.0,op,0.0,0.0)

	def getAmbient(self, node='',op=OP_DEFAULT):
		"""Get ambient color"""
		return _ipcSend(_VIZ_CHILDGET,COLOR,self.id,node,2.0,op,0.0,0.0)

	def getEmissive(self, node='',op=OP_DEFAULT):
		"""Get emissive color"""
		return _ipcSend(_VIZ_CHILDGET,COLOR,self.id,node,3.0,op,0.0,0.0)

	def getShininess(self, node='',op=OP_DEFAULT):
		"""Get the shininess"""
		return _ipcSend(_VIZ_CHILDGET,COLOR,self.id,node,4.0,op,0.0,0.0)[0]

	def getAlpha(self, node='',op=OP_DEFAULT,mode=COLOR_DIFFUSE):
		"""Get node alpha"""
		return _ipcSend(_VIZ_CHILDGET,ALPHA,self.id,node,mode,op,0.0,0.0)

	def getChildren(self):
		"""Get child nodes"""
		results = _ipcSend(_VIZ_CHILDGET,CHILDREN,self.id,'',0.0,0.0,0.0,0.0)
		return [ _GetNode(id) for id in results ]

	def getParents(self):
		"""Get parent nodes"""
		results = _ipcSend(_VIZ_CHILDGET,PARENTS,self.id,'',0.0,0.0,0.0,0.0)
		return [ _GetNode(id) for id in results ]

	def isChild(self,other):
		"""Returns whether the other node is a child of this node"""
		return _ipcSend(_VIZ_CHILDGET,_ISCHILD,self.id,'',other.id,0.0,0.0,0.0)

	def isParent(self,other):
		"""Returns whether the other node is a parent of this node"""
		return _ipcSend(_VIZ_CHILDGET,_ISPARENT,self.id,'',other.id,0.0,0.0,0.0)

	def getNodeNames(self, node='', op=OP_DEFAULT, flags=TYPE_ALL):
		"""Returns a list of all the node names underneath this node
		@return []"""
		return _ipcSend(_VIZ_CHILDGET,_SUBNODE_NAMES,flags,node,op,self.id,0.0,0.0)

	def getNodeCount(self, node='', op=OP_DEFAULT, flags=TYPE_ALL):
		"""Returns a count of all the node names underneath this node"""
		return _ipcSend(_VIZ_CHILDGET,98,flags,node,op,self.id,0.0,0.0)

	def getDescriptionList(self, node='', op=OP_DEFAULT):
		"""Returns a list of description strings for the sub-node with the specified name
		@return []"""
		return _ipcSend(_VIZ_CHILDGET,111,self.id,node,op,0.0,0.0,0.0)

	def getDescription(self, node='', op=OP_DEFAULT):
		"""Returns the first description string for the sub-node with the specified name
		@return ''"""
		return _ipcSend(_VIZ_CHILDGET,112,self.id,node,op,0.0,0.0,0.0)

	def getDescriptionDict(self, node='', op=OP_DEFAULT):
		"""Returns a dictionary mapping sub-node names to their description list
		@return {}"""
		return _ipcSend(_VIZ_CHILDGET,113,self.id,node,op,0.0,0.0,0.0)

	def getVisible(self, node='', op=OP_DEFAULT):
		"""Get visibility of node"""
		return _ipcSend(_VIZ_CHILDGET,VISIBLE,self.id,node,op,0.0,0.0,0.0)

	def getBillboard(self):
		"""Get billboard mode"""
		return _ipcSend(_VIZ_CHILDGET,BILLBOARD,self.id,'',0.0,0.0,0.0,0.0)

	def getAutoScale(self):
		"""Get auto scale mode"""
		return _ipcSend(_VIZ_CHILDGET,116,self.id,'',0.0,0.0,0.0,0.0)

	def getReferenceFrame(self):
		"""Get the reference frame for node transformations"""
		return _ipcSend(_VIZ_CHILDGET,121,self.id,'',0.0,0.0,0.0,0.0)

	def getMessage(self):
		"""Get node message
		@return ''"""
		return _ipcSend(_VIZ_CHILDGET,MESSAGE,self.id,'',0.0,0.0,0.0,0.0)

	def getTextOverflow(self, node=''):
		"""Get text overflow flags"""
		return _ipcSend(_VIZ_CHILDGET,127,self.id,node,0.0,0.0,0.0,0.0)

	def getFont(self):
		"""Get font of node
		@return ''"""
		return _ipcSend(_VIZ_CHILDGET,FONT,self.id,'',0.0,0.0,0.0,0.0)

	def getFontSize(self):
		"""Get the font size"""
		return _ipcSend(_VIZ_TEXTGET,self.id,3,'',0.0,0.0,0.0,0.0)

	def getFontHint(self):
		"""Get hint flag for text font"""
		return _ipcSend(_VIZ_TEXTGET,self.id,6,'',0.0,0.0,0.0,0.0)

	def getResolution(self):
		"""Get font of node"""
		return _ipcSend(_VIZ_CHILDGET,RESOLUTION,self.id,'',0.0,0.0,0.0,0.0)

	def getAlignment(self, node=''):
		"""Get node alignment"""
		return _ipcSend(_VIZ_CHILDGET,ALIGNMENT,self.id,node,0.0,0.0,0.0,0.0)

	def getLineSpacing(self):
		"""Get the line spacing percentage"""
		return _ipcSend(_VIZ_TEXTGET,self.id,1,'',0.0,0.0,0.0,0.0)

	def getBackdrop(self):
		"""Get the backdrop mode of the text"""
		return _ipcSend(_VIZ_TEXTGET,self.id,4,'',0.0,0.0,0.0,0.0)

	def getBackdropOffset(self):
		"""Get the backdrop offset amount of the text"""
		return _ipcSend(_VIZ_TEXTGET,self.id,5,'',0.0,0.0,0.0,0.0)

	def getBackdropColor(self):
		"""Get the backdrop color of the text"""
		return self.getColor(mode=COLOR_BACKDROP)

	def getBackdropAlpha(self):
		"""Get the backdrop alpha of the text"""
		return self.getAlpha(mode=COLOR_BACKDROP)

	def getFilename(self):
		"""Get the filename of the node
		@return ''"""
		return _ipcSend(_VIZ_CHILDGET,FILENAME,self.id,'',0.0,0.0,0.0,0.0)

	def setPosition(self,x,y=ABSOLUTE,z=0,mode=ABSOLUTE):
		"""translate the node"""
		if _islist(x):
			_ipcSend(_VIZ_TRANSLATECHILD,self.id,y,'',x[0],x[1],x[2],0.0)
		else:
			_ipcSend(_VIZ_TRANSLATECHILD,self.id,mode,'',x,y,z,0.0)

	def setEuler(self, x, y=ABSOLUTE, z=0, mode = ABSOLUTE):
		"""Set euler rotation"""
		if _islist(x):
			_ipcSend(_VIZ_ROTCHILDEULER,self.id,y,'',x[0],x[1],x[2],0.0)
		else:
			_ipcSend(_VIZ_ROTCHILDEULER,self.id,mode,'',x,y,z,0.0)

	def setAxisAngle(self, x, y=ABSOLUTE, z=0, deg=0, mode = ABSOLUTE):
		"""Set Axis-Angle rotation"""
		if _islist(x):
			_ipcSend(_VIZ_ROTATECHILD,self.id,y,'',x[0],x[1],x[2],x[3])
		else:
			_ipcSend(_VIZ_ROTATECHILD,self.id,mode,'',x,y,z,deg)

	def setQuat(self, x, y=ABSOLUTE, z=0, w=0, mode=ABSOLUTE):
		"""Set quaternion rotation"""
		if _islist(x):
			_ipcSend(_VIZ_ROTQUATCHILD,self.id,y,'',x[0],x[1],x[2],x[3])
		else:
			_ipcSend(_VIZ_ROTQUATCHILD,self.id,mode,'',x,y,z,w)

	@DeprecateObject
	def lookat(self,x, y=0, z=ABSOLUTE, roll=0, mode=ABSOLUTE):
		"""Make the node face the given point"""
		if _islist(x):
			_ipcSend(_VIZ_CHILDLOOKAT,self.id,z,'',x[0],x[1],x[2],y)
		else:
			_ipcSend(_VIZ_CHILDLOOKAT,self.id,mode,'',x,y,z,roll)

	def lookAt(self, point, roll=0.0, mode=ABS_PARENT):
		"""Set the rotation of the node to look at the specified point"""
		_ipcSend(_VIZ_CHILDLOOKAT,self.id,mode,'',point[0],point[1],point[2],roll)

	def setScale(self,x,y=ABSOLUTE,z=1,mode=ABSOLUTE):
		"""Scale the node"""
		if _islist(x):
			_ipcSend(_VIZ_SCALECHILD,self.id,y,'',x[0],x[1],x[2],0.0)
		else:
			_ipcSend(_VIZ_SCALECHILD,self.id,mode,'',x,y,z,0.0)

	def setAutoScale(self, mode):
		"""Set auto scale mode"""
		_ipcSend(_VIZ_BILLBOARDNODE,self.id,mode,'',0.0,0.0,0.0,1.0)

	def setReferenceFrame(self, mode):
		"""Set the reference frame for node transformations"""
		_ipcSend(_VIZ_BILLBOARDNODE,self.id,mode,'',0.0,0.0,0.0,2.0)

	def setCenter(self,x,y=0,z=0):
		"""Set the rotational center of the node"""
		if _islist(x):
			_ipcSend(_VIZ_CENTERCHILD,self.id,0,'',x[0],x[1],x[2],0.0)
		else:
			_ipcSend(_VIZ_CENTERCHILD,self.id,0,'',x,y,z,0.0)

	def setBoxTransform(self, flags):
		"""Set box transform flags"""
		_ipcSend(_VIZ_NODEBOXSET,self.id,1,'', flags, 0.0, 0.0, 0.0)

	def getBoxTransform(self):
		"""Get box transform flags"""
		return _ipcSend(_VIZ_CHILDGET,123,self.id,'',0.0,0.0,0.0,0.0)

	def setBoxPivot(self, pivot):
		"""Set box transform (x,y) pivot"""
		_ipcSend(_VIZ_NODEBOXSET,self.id,2,'', pivot[0], pivot[1], 0.0, 0.0)

	def getBoxPivot(self):
		"""Get box transform (x,y) pivot"""
		return _ipcSend(_VIZ_CHILDGET,124,self.id,'',0.0,0.0,0.0,0.0)

	def setBoxAnchor(self, anchor):
		"""Set box transform (left, bottom, right, top) anchor points"""
		_ipcSend(_VIZ_NODEBOXSET,self.id,3,'', anchor[0], anchor[1], anchor[2], anchor[3])

	def getBoxAnchor(self):
		"""Get box transform (left, bottom, right, top) anchor points"""
		return _ipcSend(_VIZ_CHILDGET,125,self.id,'',0.0,0.0,0.0,0.0)

	def setBoxOffset(self, rect):
		"""Set box transform (left, bottom, right, top) offsets relative to anchor position"""
		_ipcSend(_VIZ_NODEBOXSET,self.id,4,'', rect[0], rect[1], rect[2], rect[3])

	def getBoxOffset(self):
		"""Get box transform (left, bottom, right, top) offsets relative to anchor position"""
		return _ipcSend(_VIZ_CHILDGET,126,self.id,'',0.0,0.0,0.0,0.0)

	def setMask(self,mask,node='',mode=MASK_SET,op=OP_DEFAULT):
		"""Set the node mask"""
		_ipcSend(_VIZ_SETNODEMASK,self.id,mask,node,mode,op,0.0,0.0)

	def getMask(self,node='',op=OP_DEFAULT):
		"""Get the node mask"""
		return _ipcSend(_VIZ_CHILDGET,_NODE_MASK,self.id,node,op,0.0,0.0,0.0)

	def setOpMode(self,mode):
		"""Set the default op mode for all appearance commands"""
		_ipcSend(_VIZ_SETOPMODE,self.id,mode,'',0.0,0.0,0.0,0.0)

	def getOpMode(self):
		"""Get the default op mode for all appearance commands"""
		return _ipcSend(_VIZ_CHILDGET,_OP_MODE,self.id,'',0.0,0.0,0.0,0.0)

	def setTagList(self, tags, mode=MASK_SET, node='', op=OP_DEFAULT):
		"""Set the tag list"""
		if _islist(tags):
			tags = _NAME_DELIMETER.join(tags)
		_ipcSend(_VIZ_SETSTRING,0,0,tags,0.0,0.0,0.0,0.0)
		_ipcSend(_VIZ_NODESETTAG, self.id, mode, node, op, 0.0, 0.0, 0.0)

	def addTag(self, tags, node='', op=OP_DEFAULT):
		"""Add tags to the tag list"""
		self.setTagList(tags, mode=MASK_ADD, node=node, op=op)

	def removeTag(self, tags, node='', op=OP_DEFAULT):
		"""Remove tags from the tag list"""
		self.setTagList(tags, mode=MASK_REMOVE, node=node, op=op)

	def getTagList(self, node='', op=OP_DEFAULT):
		"""Get the tag list"""
		return _ipcSend(_VIZ_CHILDGET,132,self.id,node,op,0.0,0.0,0.0)

	def hasAllTags(self, tags, node='', op=OP_DEFAULT):
		"""Return whether the node contains all of the specified tags"""
		if _islist(tags):
			tags = _NAME_DELIMETER.join(tags)
		_ipcSend(_VIZ_SETSTRING,0,0,tags,0.0,0.0,0.0,0.0)
		return _ipcSend(_VIZ_CHILDGET,134,self.id,node,op,TAG_HAS_ALL,0.0,0.0)

	def hasAnyTags(self, tags, node='', op=OP_DEFAULT):
		"""Return whether the node contains any of the specified tags"""
		if _islist(tags):
			tags = _NAME_DELIMETER.join(tags)
		_ipcSend(_VIZ_SETSTRING,0,0,tags,0.0,0.0,0.0,0.0)
		return _ipcSend(_VIZ_CHILDGET,134,self.id,node,op,TAG_HAS_ANY,0.0,0.0)

	def setTagRender(self, tags, mode, node='', op=OP_DEFAULT):
		"""Set render mode for tag"""
		if _islist(tags):
			tags = _NAME_DELIMETER.join(tags)
		_ipcSend(_VIZ_SETSTRING,0,0,tags,0.0,0.0,0.0,0.0)
		_ipcSend(_VIZ_SETTAGRENDER, self.id, mode, node, op, 0.0, 0.0, 0.0)

	def getTagRender(self, tag, node='', op=OP_DEFAULT):
		"""Get render mode for tag"""
		_ipcSend(_VIZ_SETSTRING,0,0,tag,0.0,0.0,0.0,0.0)
		return _ipcSend(_VIZ_CHILDGET,133,self.id,node,op,0.0,0.0,0.0)

	def getAsyncStatus(self):
		"""Get status of async loaded model"""
		return _ipcSend(_VIZ_CHILDGET,120,self.id,'',0.0,0.0,0.0,0.0)

	def visible(self, state = ON, node='', op=OP_DEFAULT):
		"""Set the visibility of the node, ON or OFF"""
		_ipcSend(_VIZ_SHOWCHILD,self.id,state,node,op,0.0,0.0,0.0)

	def renderToBackground(self, order=9, node=''):
		"""Render the node to the background. Used to simulate infinitely far geometry (i.e. skydomes)"""
		self.depthRange(1, 1, node=node)
		self.depthFunc(GL_LEQUAL, node=node)
		self.disable(DEPTH_WRITE, node=node)
		self.disable(ADJUST_AUTO_CLIP, node=node)
		self.drawOrder(order, node=node, op=OP_ROOT)

	def renderToEye(self, eye, node = '', op=OP_DEFAULT):
		"""Set which eye to render the node to"""
		self.setMode( eye & LEFT_EYE , RENDER_LEFT, node=node, op=op )
		self.setMode( eye & RIGHT_EYE , RENDER_RIGHT, node=node, op=op )

	def setRenderToWindow(self,mode,windows=(),allowRenderNodes=False):
		"""Control which windows the node will be rendered to"""
		_ipcSend(_VIZ_RENDERTOWINDOW,0,self.id,'',mode,allowRenderNodes,0.0,0.0)
		for w in windows:
			_ipcSend(_VIZ_RENDERTOWINDOW,1,self.id,'',w.id,0.0,0.0,0.0)

	def renderToAllWindows(self,allowRenderNodes=False):
		"""Allow the node to be rendered to all windows"""
		self.setRenderToWindow(RENDER_TO_ALL,allowRenderNodes=allowRenderNodes)

	def renderToAllWindowsExcept(self,windows,allowRenderNodes=False):
		"""Allow the node to be rendered to all windows except the specified ones"""
		self.setRenderToWindow(RENDER_TO_ALL_EXCEPT,windows,allowRenderNodes=allowRenderNodes)

	def renderOnlyToWindows(self,windows,allowRenderNodes=False):
		"""Allow the node to only be rendered to the specified windows"""
		self.setRenderToWindow(RENDER_TO_ONLY,windows,allowRenderNodes=allowRenderNodes)

	def setRenderToRenderNode(self,mode,renderNodes=(),excludeMainPass=False):
		"""Control which render nodes the node will be rendered to"""
		_ipcSend(_VIZ_RENDERTOWINDOW,2,self.id,'',mode,excludeMainPass,0.0,0.0)
		for rn in renderNodes:
			_ipcSend(_VIZ_RENDERTOWINDOW,3,self.id,'',rn.id,0.0,0.0,0.0)

	def renderToAllRenderNodes(self,excludeMainPass=False):
		"""Allow the node to be rendered to all render nodes"""
		self.setRenderToRenderNode(RENDER_TO_ALL,excludeMainPass=excludeMainPass)

	def renderToAllRenderNodesExcept(self,renderNodes,excludeMainPass=False):
		"""Allow the node to be rendered to all render nodes except the specified ones"""
		self.setRenderToRenderNode(RENDER_TO_ALL_EXCEPT,renderNodes,excludeMainPass=excludeMainPass)

	def renderOnlyToRenderNodes(self,renderNodes,excludeMainPass=False):
		"""Allow the node to only be rendered to the specified render nodes"""
		self.setRenderToRenderNode(RENDER_TO_ONLY,renderNodes,excludeMainPass=excludeMainPass)

	def setRenderLimit(self,mode):
		"""Set the render limit mode"""
		_ipcSend(_VIZ_RENDERTOWINDOW,4,self.id,'',mode,0.0,0.0,0.0)

	def setModal(self,mode):
		"""Set modal mode for GUI interaction"""
		_ipcSend(_VIZ_GUISETMODAL,self.id,mode,'',0.0,0.0,0.0,0.0)

	def clearAttribute(self, attribute, node='', unit=0, op=OP_DEFAULT):
		"""Clear an appearance attribute from the node"""
		_ipcSend(_VIZ_CLEARATTRIBUTE,self.id,attribute,node,unit,op,0.0,0.0)

	def clearUniform(self, name, node='', op=OP_DEFAULT):
		"""Clear all uniforms with the specified name from the node"""
		_ipcSend(_VIZ_SETSTRING,0,0,name,0.0,0.0,0.0,0.0)
		_ipcSend(_VIZ_CLEARATTRIBUTE,self.id,op,node,0.0,0.0,0.0,1.0)

	def clearEffectType(self, typeName, node='', op=OP_DEFAULT):
		"""Clear all effects with the specified type name from the node"""
		_ipcSend(_VIZ_SETSTRING,0,0,typeName,0.0,0.0,0.0,0.0)
		_ipcSend(_VIZ_CLEARATTRIBUTE,self.id,op,node,0.0,0.0,0.0,2.0)

	def disableEffectType(self, typeName, node='', op=OP_DEFAULT):
		"""Prevent global effects with the specified type name from affecting the node"""
		_ipcSend(_VIZ_SETSTRING,0,0,typeName,0.0,0.0,0.0,0.0)
		_ipcSend(_VIZ_CLEARATTRIBUTE,self.id,op,node,0.0,0.0,0.0,3.0)

	def setMode(self, state, mode, node = '', op=OP_DEFAULT, unit=0):
		"""Set a mode on a node"""
		if _islist(mode):
			for m in mode:
				_ipcSend(_VIZ_SETNODEMODE,self.id,m,node,state,op,unit,0.0)
		else:
			_ipcSend(_VIZ_SETNODEMODE,self.id,mode,node,state,op,unit,0.0)

	def enable(self, mode, node = '', op=OP_DEFAULT, unit=0):
		"""Enable certain attributes on the node"""
		self.setMode(True,mode,node,op,unit)

	def disable(self, mode, node = '', op=OP_DEFAULT, unit=0):
		"""Disable certain attributes on the node"""
		self.setMode(False,mode,node,op,unit)

	def setEncoding(self, mode):
		"""Set encoding for text"""
		_ipcSend(_VIZ_TEXTENCODING,self.id,mode,'',0.0,0.0,0.0,0.0)

	def message(self,value):
		"""Set the message of the text"""
		_ipcSend(_VIZ_TEXTVALUE,self.id,0,value,0.0,0.0,0.0,0.0)

	def setTextOverflow(self, flags, node=''):
		"""Set text overflow flags"""
		_ipcSend(_VIZ_OVERFLOWMODE,self.id,flags,node,0.0,0.0,0.0,0.0)

	def alignment(self,alignment, node = ''):
		"""Set the alignment of the text"""
		_ipcSend(_VIZ_TEXTALIGN,self.id,alignment,node,0.0,0.0,0.0,0.0)

	def font(self,font):
		"""Set the font of the text"""
		return _ipcSend(_VIZ_TEXTFONT,self.id,0,font,0.0,0.0,0.0,0.0)

	def fontSize(self, size):
		"""Set the size of the font"""
		_ipcSend(_VIZ_SETFONTSIZE,self.id,0,'',size,0.0,0.0,0.0)

	def setFontHint(self, hint, mode=MASK_SET):
		"""Set hint flag for text font"""
		_ipcSend(_VIZ_TEXTSET,self.id,6,'',hint,mode,0.0,0.0)

	def resolution(self,res):
		"""Set the resolution of the text"""
		_ipcSend(_VIZ_TEXTRES,self.id,0,'',res,0.0,0.0,0.0)

	def setLineSpacing(self,spacing):
		"""Set the line spacing of the text as a percentage of character height"""
		_ipcSend(_VIZ_TEXTSET,self.id,1,'',spacing,0.0,0.0,0.0)

	def setBackdrop(self,mode):
		"""Set the backdrop mode of the text"""
		_ipcSend(_VIZ_TEXTSET,self.id,3,'',mode,0.0,0.0,0.0)

	def setBackdropOffset(self,offset):
		"""Set the backdrop offset amount of the text"""
		_ipcSend(_VIZ_TEXTSET,self.id,4,'',offset,0.0,0.0,0.0)

	def setBackdropColor(self, color):
		"""Set the backdrop color of the text"""
		self.color(color, mode=COLOR_BACKDROP)

	def setBackdropAlpha(self, alpha):
		"""Set the backdrop alpha of the text"""
		self.alpha(alpha, mode=COLOR_BACKDROP)

	def hint(self, flag, node = '', op=OP_DEFAULT):
		"""Set hint flags for rendering the node"""
		_ipcSend(_VIZ_HINTSCENE,self.id,1,node,flag,op,0.0,0.0)

	def hasparticles(self):
		"""Inform Vizard that the node contains particles"""
		self.hint(PARTICLE_HINT)

	def intersect(self,lineBegin, lineEnd, all=False, mode=REL_PARENT, ignoreBackFace=False, computePath=False, ignoreClipped=False, radius=0):
		"""intersect(lineBegin,lineEnd)
		Perform an intersection on the world with a line
		specified by 'lineBegin' and 'lineEnd'.
		This will return a Intersect object
		@return Intersect()"""

		flag = 0
		if not all:
			flag |= _INTERSECT_NEAREST
		if ignoreBackFace:
			flag |= _INTERSECT_IGNORE_BACK_FACE
		if computePath:
			flag |= _INTERSECT_COMPUTE_PATH
		if ignoreClipped:
			flag |= _INTERSECT_IGNORE_CLIPPED

		_ipcSend(_VIZ_SETLINEBEGIN,0,0,'',lineBegin[0],lineBegin[1],lineBegin[2],radius)

		return _ipcSend(_VIZ_NODEINTERSECT,self.id,mode,'',lineEnd[0],lineEnd[1],lineEnd[2],flag)

	def playsound(self, filename, flag=PLAY, node=''):
		"""Play a sound attached to the node in 3D"""
		_ipcSend(_VIZ_SOUNDCHILD,0,0,node,0.0,0.0,0.0,1.0)
		return VizSound3D(_ipcSend(_VIZ_SOUNDCHILD,self.id,flag,filename,0.0,0.0,0.0,0.0))

	def color(self,r,g='',b=0,node='',op=OP_DEFAULT,mode=COLOR_DIFFUSE):
		"""Set the diffuse color of the node"""
		if _islist(r):
			_ipcSend(_VIZ_CHILDCOLOR,self.id,mode,g,r[0],r[1],r[2],op)
		else:
			_ipcSend(_VIZ_CHILDCOLOR,self.id,mode,node,r,g,b,op)

	def specular(self,r,g='',b=0,node='',op=OP_DEFAULT):
		"""Set the specular color of the node"""
		if _islist(r):
			_ipcSend(_VIZ_CHILDCOLOR,self.id,1,g,r[0],r[1],r[2],op)
		else:
			_ipcSend(_VIZ_CHILDCOLOR,self.id,1,node,r,g,b,op)

	def ambient(self,r,g='',b=0,node='',op=OP_DEFAULT):
		"""Set the ambient color of the node"""
		if _islist(r):
			_ipcSend(_VIZ_CHILDCOLOR,self.id,2,g,r[0],r[1],r[2],op)
		else:
			_ipcSend(_VIZ_CHILDCOLOR,self.id,2,node,r,g,b,op)

	def emissive(self,r,g='',b=0,node='',op=OP_DEFAULT):
		"""Set the emissive color of the node"""
		if _islist(r):
			_ipcSend(_VIZ_CHILDCOLOR,self.id,3,g,r[0],r[1],r[2],op)
		else:
			_ipcSend(_VIZ_CHILDCOLOR,self.id,3,node,r,g,b,op)

	def shininess(self,val,node='',op=OP_DEFAULT):
		"""Set the shininess of the node"""
		_ipcSend(_VIZ_CHILDCOLOR,self.id,4,node,val,0.0,0.0,op)

	def alpha(self, alpha, node='', op=OP_DEFAULT, mode=COLOR_DIFFUSE):
		"""Set the alpha value of the node"""
		_ipcSend(_VIZ_CHILDALPHA,self.id,mode,node,alpha,op,0.0,0.0)

	def drawOrder(self,order,node='',bin=BIN_OPAQUE,op=OP_DEFAULT):
		"""Set the draw order for the node"""
		_ipcSend(_VIZ_DRAWORDER,self.id,order,node,bin,op,0.0,0.0)

	def setOpaqueDrawOrder(self,node='',op=OP_DEFAULT):
		"""Set the draw order of the node to the default opaque draw order"""
		self.drawOrder(0,node,BIN_OPAQUE,op)

	def setTransparentDrawOrder(self,node='',op=OP_DEFAULT):
		"""Set the draw order of the node to the default transparent draw order"""
		self.drawOrder(10,node,BIN_TRANSPARENT,op)

	def zoffset(self,factor=-1,units=0,node='',op=OP_DEFAULT):
		"""Set the z offset of the node"""
		_ipcSend(_VIZ_NODEPOLY,self.id,0,node,units,factor,0.0,op)

	def polyMode(self,mode,node='',op=OP_DEFAULT):
		"""Set polygon render mode"""
		_ipcSend(_VIZ_NODEPOLY,self.id,1,node,mode,0.0,0.0,op)

	def lineWidth(self,width,node='',op=OP_DEFAULT):
		"""Set line width of node"""
		_ipcSend(_VIZ_NODEPOLY,self.id,2,node,width,0.0,0.0,op)

	def pointSize(self,size,node='',op=OP_DEFAULT):
		"""Set point size of node"""
		_ipcSend(_VIZ_NODEPOLY,self.id,3,node,size,0.0,0.0,op)

	def clipPlane(self,plane,num=0,mode=CLIP_GLOBAL,node='',op=OP_DEFAULT):
		"""Add a clip plane to the node"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', plane[0],plane[1],plane[2],plane[3])
		_ipcSend(_VIZ_NODECLIPPLANE,self.id,num,node,op,mode,0.0,0.0)

	def appearance(self, flags = 0, node = '', unit = 0, op=OP_DEFAULT):
		"""Set the texture appearance of the node"""
		_ipcSend(_VIZ_SETAPPEARANCE,self.id,flags,node,unit,op,0.0,0.0)

	def texblend(self, blend, node = '', unit = 0, op=OP_DEFAULT):
		"""Set the amount to blend between the current and previous texture"""
		tc = TextureCombine()
		tc.blend(blend)
		self.texCombine(tc,node,unit,op)

	def texCombine(self, tc, node = '', unit = 0, op=OP_DEFAULT):
		"""Set the texture combiner for the specified texture unit"""
		_ipcSend(_VIZ_TEXBLEND,0,tc.combine_rgb,'',tc.source0_rgb,tc.source1_rgb,tc.source2_rgb,tc.constant_color[0])
		_ipcSend(_VIZ_TEXBLEND,1,tc.combine_alpha,'',tc.source0_alpha,tc.source1_alpha,tc.source2_alpha,tc.constant_color[1])
		_ipcSend(_VIZ_TEXBLEND,2,0,'',tc.operand0_rgb,tc.operand1_rgb,tc.operand2_rgb,tc.constant_color[2])
		_ipcSend(_VIZ_TEXBLEND,3,0,'',tc.operand0_alpha,tc.operand1_alpha,tc.operand2_alpha,tc.constant_color[3])
		_ipcSend(_VIZ_TEXBLEND,4,self.id,node,unit,op,tc.scale_rgb,tc.scale_alpha)

	def texGen(self, tg, node = '', unit = 0, op=OP_DEFAULT):
		"""Set the texture coordinate generator for the specified unit"""
		if isinstance(tg,TextureGen):
			m = tg.matrix
			_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', m[0], m[1], m[2], m[3])
			_ipcSend(_VIZ_SETMATRIX2, 0, 0, '', m[4], m[5], m[6], m[7])
			_ipcSend(_VIZ_SETMATRIX3, 0, 0, '', m[8], m[9], m[10], m[11])
			_ipcSend(_VIZ_SETMATRIX4, 0, 0, '', m[12], m[13], m[14], m[15])
			_ipcSend(_VIZ_NODETEXGEN,self.id,unit,node,tg.mode,op,1.0,0.0)
		else:
			_ipcSend(_VIZ_NODETEXGEN,self.id,unit,node,tg,op,0.0,0.0)

	def texmat(self, transform, node = '', unit = 0, autoScale=False, op=OP_DEFAULT):
		"""Set the texture matrix"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', transform[0], transform[1], transform[2], transform[3])
		_ipcSend(_VIZ_SETMATRIX2, 0, 0, '', transform[4], transform[5], transform[6], transform[7])
		_ipcSend(_VIZ_SETMATRIX3, 0, 0, '', transform[8], transform[9], transform[10], transform[11])
		_ipcSend(_VIZ_SETMATRIX4, 0, 0, '', transform[12], transform[13], transform[14], transform[15])
		_ipcSend(_VIZ_SETTEXMAT,self.id,unit,node,autoScale,op,0.0,0.0)

	def anisotropy(self,value, node='', unit=0, op=OP_DEFAULT):
		"""Set the texture anisotropy for node texture"""
		_ipcSend(_VIZ_NODEANISOTROPY,self.id,unit,node,value,op,0.0,0.0)

	def cullFace(self, mode, node='',op=OP_DEFAULT):
		"""Set OpenGL cull face of node"""
		_ipcSend(_VIZ_NODEGLFUNC,self.id,2,node,mode,op,0.0,0.0)

	def setTexQuadDisplayMode(self, mode, node='', op=OP_DEFAULT):
		"""Set the texture quad display mode"""
		_ipcSend(_VIZ_NODETEXSET, 1, self.id, node, mode, op, 0.0, 0.0)

	def getTexQuadDisplayMode(self, node='', op=OP_DEFAULT):
		"""Get the texture quad display mode"""
		return _ipcSend(_VIZ_CHILDGET,128,self.id,node,op,0.0,0.0,0.0)

	def setCompositeAlpha(self, alpha, node='', op=OP_DEFAULT):
		"""Set composite alpha value for node"""
		_ipcSend(_VIZ_SETCOMPALPHA, self.id, 0, node, op, alpha, 0.0, 0.0)

	def getCompositeAlpha(self, node='', op=OP_DEFAULT):
		"""Get composite alpha value for node"""
		return _ipcSend(_VIZ_CHILDGET, 131, self.id, node, op, 0.0, 0.0, 0.0)

	def depthFunc(self, mode, node='',op=OP_DEFAULT):
		"""Set OpenGL depth function of node"""
		_ipcSend(_VIZ_NODEGLFUNC,self.id,0,node,mode,op,0.0,0.0)

	def depthRange(self, nearVal, farVal, node='',op=OP_DEFAULT):
		"""Set OpenGL depth range of node"""
		_ipcSend(_VIZ_NODEGLFUNC,self.id,5,node,nearVal,farVal,op,0.0)

	def alphaFunc(self, func, ref, node='',op=OP_DEFAULT):
		"""Set OpenGL alpha function of node"""
		_ipcSend(_VIZ_NODEGLFUNC,self.id,3,node,func,ref,op,0.0)

	def blendFunc(self, src, dst, srcAlpha=AUTO_COMPUTE, dstAlpha=AUTO_COMPUTE, node='',op=OP_DEFAULT):
		"""Set OpenGL blend function of node"""
		_ipcSend(_VIZ_NODEGLFUNC,0,4,'',srcAlpha,dstAlpha,0.0,0.0)
		_ipcSend(_VIZ_NODEGLFUNC,self.id,1,node,src,dst,op,0.0)

	def blendColor(self, color, node='',op=OP_DEFAULT):
		"""Set OpenGL blend color of node"""
		if len(color) == 3:
			_ipcSend(_VIZ_NODEGLFUNC,0,6,'',color[0],color[1],color[2],1.0)
		else:
			_ipcSend(_VIZ_NODEGLFUNC,0,6,'',color[0],color[1],color[2],color[3])
		_ipcSend(_VIZ_NODEGLFUNC,self.id,7,node,op,0.0,0.0,0.0)

	def stencilFunc(self, stencil, node='',op=OP_DEFAULT):
		"""Set OpenGL stencil function of node"""
		_ipcSend(_VIZ_NODESTENCIL,1,stencil.funcMask,'',stencil.func,stencil.funcRef,0.0,0.0)
		_ipcSend(_VIZ_NODESTENCIL,2,stencil.writeMask,'',stencil.sfail,stencil.zfail,stencil.zpass,0.0)
		_ipcSend(_VIZ_NODESTENCIL,3,self.id,node,op,0.0,0.0,0.0)

	def billboard(self,mode = BILLBOARD_VIEW):
		"""Turn billboarding ON or OFF for the node"""
		_ipcSend(_VIZ_BILLBOARDNODE,self.id,mode,'',0.0,0.0,0.0,0.0)

	def texture(self, tex, node='', unit=0, coordUnit=0, name='', op=OP_DEFAULT):
		"""Apply a texture to the node"""
		if coordUnit is None:
			coordUnit = -1
		if isinstance(unit,str):
			name = unit
			unit = -1
		_ipcSend(_VIZ_SETSTRING,0,0,name,0.0,0.0,0.0,0.0)
		if isinstance(tex,VizTexture):
			_ipcSend(_VIZ_TEXTURE,self.id,tex.id,node,unit,tex._textype,op,coordUnit)
		elif tex == 0 or tex is None:
			_ipcSend(_VIZ_TEXTURE,self.id,0,node,unit,_VIZ_DEL_TEX,op,coordUnit)
		else:
			raise TypeError('texture() parameter is not a valid texture object')

	def getTexture(self,node='',unit=0,op=OP_DEFAULT):
		"""Get handle to texture that is currently applied to node
		@return VizTexture()"""
		return _ipcSend(_VIZ_GETNODETEXTURE,self.id,unit,node,op,0.0,0.0,0.0)

	@DeprecateObject
	def setScreenGrabTexture(self,tex,node='',op=OP_DEFAULT):
		"""Set a texture that will grab the contents of the screen before the object is rendered.
		This is commonly used for implementing refraction effects."""
		if isinstance(tex,VizTexture):
			_ipcSend(_VIZ_NODEGRABTEX,self.id,tex.id,node,tex._textype,op,0.0,0.0)
		elif tex == 0 or tex is None:
			_ipcSend(_VIZ_NODEGRABTEX,self.id,0,node,_VIZ_DEL_TEX,op,0.0,0.0)

	def getStats(self,node='',op=OP_DEFAULT):
		"""Returns node statistics"""
		return NodeStats(*_ipcSend(_VIZ_STATSCHILD,self.id,op,node,0.0,0.0,0.0,0.0))

	def optimize(self,flag=OPT_DEFAULT):
		"""Perform optimizations of the node"""
		_ipcSend(_VIZ_OPTIMIZECHILD,self.id,flag,'',0.0,0.0,0.0,0.0)

	def modify(self, modifier, command = 0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0):
		"""Send the node to the given modifier"""
		if isinstance(modifier,VizModifier):
			_ipcSend(_VIZ_MODIFYPARAMS,modifier.id,command,mesg,x,y,z,w)
			_ipcSend(_VIZ_MODIFY,modifier.id,self.id,'',0.0,0.0,0.0,0.0)

	def apply(self,program,node='',op=OP_DEFAULT):
		"""Apply a shader program to the node"""
		if isinstance(program,VizShader):
			_ipcSend(_VIZ_APPLYSHADER,self.id,program.id,node,op,0.0,0.0,0.0)
		elif isinstance(program,VizUniform):
			_ipcSend(_VIZ_APPLYUNIFORM,self.id,program.id,node,op,0.0,0.0,0.0)
		elif isinstance(program,VizEffect):
			_ipcSend(_VIZ_EFFECTSET,5,self.id,node,program.id,op,0.0,0.0)
		elif isinstance(program,VizEffectComposer):
			_ipcSend(_VIZ_EFFECTSET,6,self.id,node,program.id,op,0.0,0.0)

	def unapply(self, attribute, unit=AUTO_COMPUTE, node='', op=OP_DEFAULT):
		"""Unapply a shader/effect/texture object from the node"""
		if isinstance(attribute, VizTexture):
			_ipcSend(_VIZ_CLEARATTRIBUTE, self.id, attribute.id, node, op, attribute._textype, unit, 4.0)
		elif isinstance(attribute, VizShader):
			_ipcSend(_VIZ_CLEARATTRIBUTE, self.id, attribute.id, node, op, 0.0, 0.0, 5.0)
		elif isinstance(attribute, VizUniform):
			_ipcSend(_VIZ_CLEARATTRIBUTE, self.id, attribute.id, node, op, 0.0, 0.0, 6.0)
		elif isinstance(attribute, VizEffect):
			_ipcSend(_VIZ_CLEARATTRIBUTE, self.id, attribute.id, node, op, 0.0, 0.0, 7.0)
		elif isinstance(attribute, VizEffectComposer):
			_ipcSend(_VIZ_CLEARATTRIBUTE, self.id, attribute.id, node, op, 0.0, 0.0, 8.0)

	def generateEffects(self, flags=EFFECTGEN_DEFAULT, composer=None, node='', op=OP_DEFAULT):
		"""Automatically generate effects on the node based on specified flags"""
		_ipcSend(_VIZ_EFFECTSET,14,self.id,node,composer.id if composer else -1,flags,op,0.0)

	def setUniformBool(self, name, value, node='', op=OP_DEFAULT):
		"""Apply a boolean uniform value to the node"""
		if _islist(value):
			dataType = {1:UNIFORM_BOOL,2:UNIFORM_BOOL_VEC2,3:UNIFORM_BOOL_VEC3}.get(len(value),UNIFORM_BOOL_VEC4)
			value = (list(value) + [0,0,0])[:4]
		else:
			dataType = UNIFORM_BOOL
			value = [value,0,0,0]

		_ipcSend(_VIZ_NODESETUNIFORM,5,0,name,*value)
		_ipcSend(_VIZ_NODESETUNIFORM,6,self.id,node,op,dataType,0.0,0.0)

	def setUniformInt(self, name, value, node='', op=OP_DEFAULT):
		"""Apply an integer uniform value to the node"""
		if _islist(value):
			dataType = {1:UNIFORM_INT,2:UNIFORM_INT_VEC2,3:UNIFORM_INT_VEC3}.get(len(value),UNIFORM_INT_VEC4)
			value = (list(value) + [0,0,0])[:4]
		else:
			dataType = UNIFORM_INT
			value = [value,0,0,0]

		_ipcSend(_VIZ_NODESETUNIFORM,1,0,name,*value)
		_ipcSend(_VIZ_NODESETUNIFORM,2,self.id,node,op,dataType,0.0,0.0)

	def setUniformFloat(self, name, value, node='', op=OP_DEFAULT):
		"""Apply a floating point uniform value to the node"""
		if _islist(value):
			dataType = {1:UNIFORM_FLOAT,2:UNIFORM_FLOAT_VEC2,3:UNIFORM_FLOAT_VEC3}.get(len(value),UNIFORM_FLOAT_VEC4)
			value = (list(value) + [0,0,0])[:4]
		else:
			dataType = UNIFORM_FLOAT
			value = [value,0,0,0]

		_ipcSend(_VIZ_NODESETUNIFORM,3,0,name,*value)
		_ipcSend(_VIZ_NODESETUNIFORM,4,self.id,node,op,dataType,0.0,0.0)

	def setProperty(self, name, value):
		"""Set node property value"""
		if _islist(value) or isinstance(value,Matrix):
			data = list(value)
		else:
			data = [value]

		size = len(data)
		if size > 4:
			if size < 16:
				data += [0] * (16-size) # Ensure at least 16 values
			_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', *data[0:4])
			_ipcSend(_VIZ_SETMATRIX2, 0, 0, '', *data[4:8])
			_ipcSend(_VIZ_SETMATRIX3, 0, 0, '', *data[8:12])
			_ipcSend(_VIZ_NODESETUNIFORM, 8, self.id, name,data[12],data[13],data[14],data[15])
		else:
			data += [0,0,0]
			_ipcSend(_VIZ_NODESETUNIFORM, 7, self.id, name,data[0],data[1],data[2],data[3])

	def getProperty(self, name):
		"""Get node property value"""
		return _ipcSend(_VIZ_CHILDGET, 122, self.id, name,0.0,0.0,0.0,0.0)

	def setMaterial(self, filename, flags=0, node='', op=OP_DEFAULT):
		"""Set material on a node"""
		_ipcSend(_VIZ_SETSTRING,0,0,filename,0.0,0.0,0.0,0.0)
		_ipcSend(_VIZ_SETMATERIAL, self.id, flags, node, op, 0.0, 0.0, 0.0)

	def setMatrix(self, transform, mode = ABSOLUTE, node=''):
		"""Set the 4x4 matrix of the node"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', transform[0], transform[1], transform[2], transform[3])
		_ipcSend(_VIZ_SETMATRIX2, 0, 0, '', transform[4], transform[5], transform[6], transform[7])
		_ipcSend(_VIZ_SETMATRIX3, 0, 0, '', transform[8], transform[9], transform[10], transform[11])
		_ipcSend(_VIZ_SETMATRIX4, 0, 0, '', transform[12], transform[13], transform[14], transform[15])
		_ipcSend(_VIZ_SETCHILDMATRIX,self.id,mode,node,0.0,0.0,0.0,0.0)

	def resetMatrix(self, mask=LINK_ALL, mode=ABSOLUTE, node=''):
		"""Reset transform matrix of node"""
		_ipcSend(_VIZ_RESETMATRIX,self.id,mask,node,mode,0.0,0.0,0.0)

	def getTransform(self, name):
		"""Get a linkable object for controlling a sub-transform of the node
		@return VizTransformNodeLinkable()"""
		return VizTransformNodeLinkable._GetObject(_ipcSend(_VIZ_CREATELINKABLE,self.id,0,name,0.0,0.0,0.0,4.0))

	def getChild(self, name, flags=CHILD_DEFAULT, **kw):
		"""Get a sub child of a node
		@return VizNode()"""
		id, klass = _ipcSend(_VIZ_GETCHILD, self.id, 0, name, flags, 0.0, 0.0, 0.0)
		return klass._GetObject(id, **kw)

	def insertGroupAbove(self,name):
		"""Create and return group node inserted above sub-node with specified name
		@return VizGroup()"""
		return VizGroup._GetObject(_ipcSend(_VIZ_GETCHILD, self.id, 1, name, 0.0, 0.0, 0.0, 0.0))

	def insertGroupBelow(self,name):
		"""Create and return group node inserted below sub-node with specified name
		@return VizGroup()"""
		return VizGroup._GetObject(_ipcSend(_VIZ_GETCHILD, self.id, 2, name, 0.0, 0.0, 0.0, 0.0))

	@DeprecateObject
	def add(self,what,*args,**kw):
		"""Add an object underneath the node"""
		if isinstance(what,ActionData):
			self.addAction(what,*args,**kw)
		elif isinstance(what,int):
			if what == TEXT3D:
				return addText(args[0],self.id,*(args[1:]),**kw)
			elif what == TEXQUAD:
				return addTexQuad(self.id,*args,**kw)
			elif what == GROUP:
				return addGroup(self.id,*args,**kw)
			elif what == LIGHT:
				return addLight(parent=self.id,*args,**kw)
			elif what == SLIDER:
				return addSlider(1,self.id,*args,**kw)
			elif what == CHECKBOX:
				return addCheckbox(1,self.id,*args,**kw)
			elif what == BUTTON:
				return addButton(1,self.id,*args,**kw)
			elif what == RADIO:
				return addRadioButton(args[0],1,self.id,*(args[1:]),**kw)
			elif what == TEXTBOX:
				return addTextbox(1,self.id,*args,**kw)
			elif what == PROGRESS_BAR:
				return addProgressBar(args[0],1,self.id,*(args[1:]),**kw)
			elif what == BUTTON_LABEL:
				return addButtonLabel(args[0],1,self.id,*(args[1:]),**kw)
			elif what == DROPLIST:
				return addDropList(1,self.id,*args,**kw)
			else:
				raise ValueError('Unrecognized add type: '+str(what))
		else:

			fileType = _getFileExtension(what).upper()

			# VRMLs
			if fileType in _TypeModel:
				return addChild(what,self.id,*args,**kw)

			# Avatar
			elif fileType in _TypeAvatar:
				return addAvatar(what,self.id,*args,**kw)

			# Custom child plug-in
			elif fileType == 'DLC':
				return addCustomNode(what,parent=self.id,*args,**kw)

			# Viz Face File
			elif fileType in _TypeFace:
				return addFace(what,self.id,*args,**kw)

			else:
				raise ValueError('Unrecognized file extension: '+fileType)

	def copy(self, parent = WORLD, scene = MainScene, **kw):
		"""Make a copy of the node
		@return VizNode()"""
		return self.__class__(_ipcSend(_VIZ_COPYCHILD, _sceneID(scene), int(parent), '', self.id, 0.0, 0.0, 0.0),**kw)

	def clone(self, parent = WORLD, scene = MainScene, **kw):
		"""Make a clone of the node
		@return VizNode()"""
		return self.__class__(_ipcSend(_VIZ_CLONECHILD, _sceneID(scene), int(parent), '', self.id, 0.0, 0.0, 0.0),**kw)

	### Animation interface

	def getAnimationNames(self, node='', op=OP_DEFAULT):
		return _ipcSend(_VIZ_GETANIMATION,0,self.id,node,0.0,0.0,0.0,op)

	def getAnimationDuration(self, node='', op=OP_DEFAULT):
		return _ipcSend(_VIZ_GETANIMATION,1,self.id,node,0.0,0.0,0.0,op)

	def getAnimationFrameCount(self, node='', op=OP_DEFAULT):
		return _ipcSend(_VIZ_GETANIMATION,2,self.id,node,0.0,0.0,0.0,op)

	def getAnimationTime(self, node='', op=OP_DEFAULT):
		return _ipcSend(_VIZ_GETANIMATION,3,self.id,node,0.0,0.0,0.0,op)

	def setAnimationTime(self, time, node='', op=OP_DEFAULT):
		_ipcSend(_VIZ_SETANIMATION,3,self.id,node,time,0.0,0.0,op)

	def getAnimationFrame(self, node='', op=OP_DEFAULT):
		return _ipcSend(_VIZ_GETANIMATION,4,self.id,node,0.0,0.0,0.0,op)

	def setAnimationFrame(self, frame, node='', op=OP_DEFAULT):
		_ipcSend(_VIZ_SETANIMATION,4,self.id,node,frame,0.0,0.0,op)

	def getAnimationState(self, node='', op=OP_DEFAULT):
		return _ipcSend(_VIZ_GETANIMATION,5,self.id,node,0.0,0.0,0.0,op)

	def setAnimationState(self, state, node='', op=OP_DEFAULT):
		_ipcSend(_VIZ_SETANIMATION,5,self.id,node,state,0.0,0.0,op)

	def getAnimationLoopMode(self, node='', op=OP_DEFAULT):
		return _ipcSend(_VIZ_GETANIMATION,6,self.id,node,0.0,0.0,0.0,op)

	def setAnimationLoopMode(self, loopMode, node='', op=OP_DEFAULT):
		_ipcSend(_VIZ_SETANIMATION,6,self.id,node,loopMode,0.0,0.0,op)

	def getAnimationSpeed(self, node='', op=OP_DEFAULT):
		return _ipcSend(_VIZ_GETANIMATION,7,self.id,node,0.0,0.0,0.0,op)

	def setAnimationSpeed(self, speed, node='', op=OP_DEFAULT):
		_ipcSend(_VIZ_SETANIMATION,7,self.id,node,speed,0.0,0.0,op)

	###Particle System interface

	def emitParticleCount(self, count, node='', op=OP_DEFAULT):
		"""Emit the specified number of particles at the current location"""
		_ipcSend(_VIZ_CMDPARTICLE,self.id,1,node,count,0.0,0.0,op)

	def emitParticleCycle(self, node='', op=OP_DEFAULT):
		"""Emit a full particle system cycle at the current location"""
		_ipcSend(_VIZ_CMDPARTICLE,self.id,2,node,0.0,0.0,0.0,op)

	###Physics interface

	def commandPhysics(self, command = 0, mesg='', x = 0.0, y = 0.0, z = 0.0, w = 0.0):
		"""Send a custom command to the physics node"""
		_ipcSend(_VIZ_QUEUEPHYSCMD,0,command,mesg,x,y,z,w)
		return _ipcSend(_VIZ_NODECMDPHYS,1,self.id,'',0.0,0.0,0.0,0.0)

	def setVelocity(self,vel,mode=ABS_GLOBAL):
		"""Set the velocity of the node"""
		_ipcSend(_VIZ_NODEVELOCITY,self.id,mode,'',vel[0],vel[1],vel[2],0.0)

	def getVelocity(self,mode=ABS_GLOBAL):
		"""Get the velocity of the node"""
		return _ipcSend(_VIZ_CHILDGET,VELOCITY,self.id,'',mode,0.0,0.0,0.0)

	def setAngularVelocity(self,vel,mode=ABS_GLOBAL):
		"""Set the angular velocity of the node"""
		_ipcSend(_VIZ_ANGULARVEL,self.id,mode,'',vel[0],vel[1],vel[2],0.0)

	def getAngularVelocity(self,mode=ABS_GLOBAL):
		"""Get the angular velocity of the node"""
		return _ipcSend(_VIZ_CHILDGET,_ANGULAR_VEL,self.id,'',mode,0.0,0.0,0.0)

	def applyForce(self,dir,duration=0.0,mode=ABS_GLOBAL,pos=None,posMode=ABS_GLOBAL):
		"""Apply a force to the node"""
		if pos is None:
			_ipcSend(_VIZ_APPLYFORCE,self.id,mode,'',dir[0],dir[1],dir[2],duration)
		else:
			_ipcSend(_VIZ_QUEUEPHYSCMD,posMode,0,'',pos[0],pos[1],pos[2],0.0)
			_ipcSend(_VIZ_APPLYFORCEPOS,self.id,mode,'',dir[0],dir[1],dir[2],duration)

	def applyTorque(self,axis,duration=0.0,mode=ABS_GLOBAL):
		"""Apply torque to the node"""
		_ipcSend(_VIZ_APPLYTORQUE,self.id,mode,'',axis[0],axis[1],axis[2],duration)

	def collideNone(self):
		"""Clear physics definition of node"""
		_ipcSend(_VIZ_COLLIDENONE,self.id,0,'',0.0,0.0,0.0,0.0)

	def collideBox(self, x = -1, y = -1, z = -1, node='', **kw):
		"""Use a box for collision tests"""
		if _islist(x):
			return VizPhysicsShape(_ipcSend(_VIZ_COLLIDEBOX,self.id,0,node,x[0],x[1],x[2],0.0),self.id,**kw)
		return VizPhysicsShape(_ipcSend(_VIZ_COLLIDEBOX,self.id,0,node,x,y,z,0.0),self.id,**kw)

	def collideSphere(self, radius = -1, node='', **kw):
		"""Use a sphere for collision tests"""
		return VizPhysicsShape(_ipcSend(_VIZ_COLLIDESPHERE,self.id,0,node,radius,0.0,0.0,0.0),self.id,**kw)

	def collideCapsule(self, radius = -1, length = -1, node='', **kw):
		"""Use a capsule for collision tests"""
		return VizPhysicsShape(_ipcSend(_VIZ_COLLIDECAP,self.id,0,node,radius,length,0.0,0.0),self.id,**kw)

	def collideMesh(self, model=-1, node='', **kw):
		"""Use the object mesh for collision tests"""
		return VizPhysicsShape(_ipcSend(_VIZ_COLLIDEMESH,self.id,int(model),node,0.0,0.0,0.0,0.0),self.id,**kw)

	def collidePlane(self,a=0,b=1,c=0,d=0, **kw):
		"""Use a plane for collision tests"""
		if _islist(a):
			return VizPhysicsShape(_ipcSend(_VIZ_COLLIDEPLANE,self.id,0,'',a[0],a[1],a[2],a[3]),self.id,**kw)
		return VizPhysicsShape(_ipcSend(_VIZ_COLLIDEPLANE,self.id,0,'',a,b,c,d),self.id,**kw)

	def collideCustom(self, command = 0, mesg='', x = 0, y = 0, z = 0, w = 0, **kw):
		"""Use a custom collision model"""
		return VizPhysicsShape(_ipcSend(_VIZ_COLLIDECUSTOM,self.id,command,mesg,x,y,z,w),self.id,**kw)

	def collideCopy(self, node):
		"""Copy the collision definition of another node"""
		vals = _ipcSend(_VIZ_COLLIDECOPY,self.id,node.id,'',0.0,0.0,0.0,0.0)
		return [ VizPhysicsShape(id,self.id) for id in vals ]

	def collideFile(self, file):
		"""Load collision definition from a file"""
		_ipcSend(_VIZ_COLLIDEFILE,self.id,0,file,0.0,0.0,0.0,0.0)

	def getCollideShapes(self):
		"""Get list of collide shapes"""
		vals = _ipcSend(_VIZ_CHILDGET,_SHAPE_LIST,self.id,'',0.0,0.0,0.0,0.0)
		return [ VizPhysicsShape(id,self.id) for id in vals ]

	"""OPAL specific functions"""
	def setLinearDamping(self,val):
		"""Set linear damping of movement"""
		self.commandPhysics(24,'',val)

	def setAngularDamping(self,val):
		"""Set angular damping of movement"""
		self.commandPhysics(25,'',val)

	class OpalMotor(VizObject):
		def __init__(self, id, func):
			VizObject.__init__(self, id)
			self._func = func

		def remove(self):
			"""Remove the spring"""
			self._func(11,'',self.id)
			self.id = -1

		def setEnabled(self,mode):
			"""Enable/Disable the spring"""
			self._func(12,'',self.id,mode)

		def enable(self):
			"""Enable the spring"""
			self.setEnabled(1)

		def disable(self):
			"""Disable the spring"""
			self.setEnabled(0)

	class OpalThrusterMotor(OpalMotor):
		def __init__(self, id, func,force=None,mode=ABS_GLOBAL,pos=None,posMode=ABS_GLOBAL,torque=None):
			VizNode.OpalMotor.__init__(self,id,func)

			if self.valid():
				if force is not None:
					self.setForce(force,mode,pos,posMode)
				elif torque is not None:
					self.setTorque(torque,mode)

		def setForce(self,dir,mode=ABS_GLOBAL,pos=None,posMode=ABS_GLOBAL):
			"""Set the force of the thruster"""
			if pos is None:
				self._func(0,'',self.id)
				self._func(17,'',dir[0],dir[1],dir[2],mode)
			else:
				self._func(0,'',self.id)
				self._func(-1,'',pos[0],pos[1],pos[2],posMode)
				self._func(19,'',dir[0],dir[1],dir[2],mode)

		def setTorque(self,axis,mode=ABS_GLOBAL):
			"""Set the torque of the thruster"""
			self._func(0,'',self.id)
			self._func(18,'',axis[0],axis[1],axis[2],mode)

	def addThruster(self,**kw):
		"""Create a motor that will apply a constant force on a physics object"""
		val = self.commandPhysics(16)
		if val is None:
			logError('** ERROR: Failed to create thruster motor')
			return None
		return VizNode.OpalThrusterMotor(val,self.commandPhysics,**kw)

	class OpalVelocityMotor(OpalMotor):
		def __init__(self, id, func, velocity=None, maxForce=None, gravity=None):
			VizNode.OpalMotor.__init__(self,id,func)

			if self.valid():
				if velocity is not None:
					self.setVelocity(velocity)
				if maxForce is not None:
					self.setMaxForce(maxForce)
				if gravity is not None:
					self.setGravity(gravity)

		def setVelocity(self,vel):
			"""Set velocity of motor"""
			self._func(14,'',self.id,vel[0],vel[1],vel[2])

		def setMaxForce(self,force):
			"""Set max force of motor"""
			self._func(15,'',self.id,force)

		def setGravity(self,mode):
			"""Set whether gravity will affect the motor"""
			self._func(20,'',self.id,mode)

	def addVelocity(self,**kw):
		"""Create a motor that will try to achieve a desried velocity
		A maximum force of 'maxForce' will be applied to achieve the velocity"""
		val = self.commandPhysics(13)
		if val is None:
			logError('** ERROR: Failed to create velocity motor')
			return None
		return VizNode.OpalVelocityMotor(val,self.commandPhysics,**kw)

	class OpalAttractorMotor(OpalMotor):
		def __init__(self, id, func, strength=None, exp=None):
			VizNode.OpalMotor.__init__(self,id,func)

			if self.valid():
				if strength is not None:
					self.setStrength(strength)
				if exp is not None:
					self.setExp(exp)

		def setStrength(self,val):
			"""Set the strength of the attraction"""
			self._func(22,'',self.id,val)

		def setExp(self,val):
			"""Set the exponent of the attraction"""
			self._func(23,'',self.id,val)

	def addAttractor(self,node,**kw):
		"""Create a motor that will simulate gravitational attraction between two objects.
		Uses the equation: magnitude = (strength * m0 * m1) / distance^exponent"""
		node.commandPhysics(-2)
		val = self.commandPhysics(21)
		if val is None:
			logError('** ERROR: Failed to create attractor motor')
			return None
		return VizNode.OpalAttractorMotor(val,self.commandPhysics,**kw)

	class OpalSpring(OpalMotor):
		def __init__(self, id, func, offset=None, linearKd=None, linearKs=None, angularKd=None, angularKs=None):
			VizNode.OpalMotor.__init__(self,id,func)

			if self.valid():
				if offset is not None:
					self.setOffset(offset)
				if linearKd is not None:
					self.setLinearKd(linearKd)
				if linearKs is not None:
					self.setLinearKs(linearKs)
				if angularKd is not None:
					self.setAngularKd(angularKd)
				if angularKs is not None:
					self.setAngularKs(angularKs)

		def setLinearKd(self, val):
			"""Set linear damping constant for spring"""
			self._func(4,'',self.id,val)

		def setLinearKs(self, val):
			"""Set linear spring constant for spring"""
			self._func(5,'',self.id,val)

		def setAngularKd(self, val):
			"""Set angular damping constant for spring"""
			self._func(6,'',self.id,val)

		def setAngularKs(self, val):
			"""Set angular spring constant for spring"""
			self._func(7,'',self.id,val)

		def setPosition(self, pos):
			"""Set position for physics node to spring to"""
			self._func(2,'',pos[0],pos[1],pos[2],self.id)

		def setQuat(self, quat):
			"""Set quaternion rotation for physics node to spring to"""
			self._func(0,'',self.id)
			self._func(3,'',quat[0],quat[1],quat[2],quat[3])

		def setOffset(self, offset, mode = ABS_GLOBAL):
			"""Set the offset position of the spring"""
			self._func(0,'',self.id)
			self._func(10,'',offset[0],offset[1],offset[2],mode)

	def addSpring(self, mode, **kw):
		"""Create a spring that is attached to the physics object"""
		val = self.commandPhysics(1,'',mode)
		if val is None:
			logError('** ERROR: Failed to create spring motor')
			return None
		return VizNode.OpalSpring(val,self.commandPhysics,**kw)

	def collidingwith(self, other, info=0):
		"""Test if the node is colliding with another node"""
		return _ipcSend(_VIZ_COLLIDINGCHILD,self.id,other.id,'',info,0.0,0.0,0.0)

_GetNode = DeprecateObject(VizNode._GetObject) #backwards compatibility

class VizLight(VizNode):
	"""VizLight object"""
	def __init__(self,id,**kw):
		VizNode.__init__(self,id,**kw)

	def position(self, x, y, z, w = 1):
		"""Set the position of the light"""
		_ipcSend(_VIZ_LIGHTPOS,self.id,0,'',x,y,z,w)

	def direction(self, vx, vy, vz):
		"""Set the direction of the light"""
		_ipcSend(_VIZ_LIGHTDIR,self.id,0,'',vx,vy,vz,0.0)

	@DeprecateObject
	def spotexponent(self, exponent):
		"""Set the spot exponent of the light"""
		_ipcSend(_VIZ_LIGHTEXP,self.id,0,'',exponent,0.0,0.0,0.0)

	@DeprecateObject
	def spread(self, angle):
		"""Set the spread angle of the light"""
		_ipcSend(_VIZ_LIGHTCUTOFF,self.id,0,'',angle,0.0,0.0,0.0)

	@DeprecateObject
	def intensity(self, intensity):
		"""Set the intensity of the light"""
		_ipcSend(_VIZ_LIGHTINTENSITY,self.id,0,'',intensity,0.0,0.0,0.0)

	@DeprecateObject
	def constantAttenuation(self, value):
		_ipcSend(_VIZ_LIGHTCONSTANT,self.id,0,'',value,0.0,0.0,0.0)

	@DeprecateObject
	def linearAttenuation(self,value):
		_ipcSend(_VIZ_LIGHTLINEAR,self.id,0,'',value,0.0,0.0,0.0)

	@DeprecateObject
	def quadraticAttenuation(self,value):
		_ipcSend(_VIZ_LIGHTQUAD,self.id,0,'',value,0.0,0.0,0.0)

	def enable(self,*args,**kw):
		"""Enable the light"""
		if args:
			VizNode.enable(self,*args,**kw)
		else:
			_ipcSend(_VIZ_LIGHTSHOW,self.id,1,'',0.0,0.0,0.0,0.0)

	def disable(self,*args,**kw):
		"""Disable the light"""
		if args:
			VizNode.disable(self,*args,**kw)
		else:
			_ipcSend(_VIZ_LIGHTSHOW,self.id,0,'',0.0,0.0,0.0,0.0)

	def getEnabled(self):
		"""Return whether the light is enabled"""
		return _ipcSend(_VIZ_CHILDGET,118,self.id,'',0.0,0.0,0.0,0.0)

	def getNumber(self):
		"""Get the OpenGL light number of the light"""
		return _ipcSend(_VIZ_CHILDGET,_LIGHT_NUMBER,self.id,'',0.0,0.0,0.0,0.0)

	def setSpotAngle(self, angle):
		"""Set the spread angle of the light"""
		_ipcSend(_VIZ_LIGHTSET,2,self.id,'',angle,0.0,0.0,0.0)

	def getSpotAngle(self):
		"""Get the spread angle of the light"""
		return _ipcSend(_VIZ_LIGHTGET,2,self.id,'',0.0,0.0,0.0,0.0)

	def setSpotPenumbra(self, penumbra):
		"""Set the percent of the spot light edge that will be softened"""
		_ipcSend(_VIZ_LIGHTSET,3,self.id,'',penumbra,0.0,0.0,0.0)

	def getSpotPenumbra(self):
		"""Get the percent of the spot light edge that will be softened"""
		return _ipcSend(_VIZ_LIGHTGET,3,self.id,'',0.0,0.0,0.0,0.0)

	def setFalloff(self, falloff):
		"""Set the falloff exponent, the rate at which the light decays over distance
		0 - No falloff
		1 - Inverse falloff
		2 - Inverse square falloff"""
		_ipcSend(_VIZ_LIGHTSET,4,self.id,'',falloff,0.0,0.0,0.0)

	def getFalloff(self):
		"""Get the falloff exponent, the rate at which the light decays over distance"""
		return _ipcSend(_VIZ_LIGHTGET,4,self.id,'',0.0,0.0,0.0,0.0)

	def setIntensity(self, intensity):
		"""Set the luminous intensity of the light"""
		_ipcSend(_VIZ_LIGHTSET,5,self.id,'',intensity,0.0,0.0,0.0)

	def getIntensity(self):
		"""Get the luminous intensity of the light"""
		return _ipcSend(_VIZ_LIGHTGET,5,self.id,'',0.0,0.0,0.0,0.0)

	def setShadowMode(self, mode):
		"""Set shadow mode of light"""
		_ipcSend(_VIZ_LIGHTSET,1,self.id,'',mode,0.0,0.0,0.0)

	def getShadowMode(self):
		"""Get shadow mode of light"""
		return _ipcSend(_VIZ_LIGHTGET,1,self.id,'',0.0,0.0,0.0,0.0)

	def setShadowTextureSize(self, size):
		"""Set the size of the shadow texture"""
		self.setProperty('shadow_texture_size',size)

	def getShadowTextureSize(self):
		"""Get the size of the shadow texture"""
		return int(self.getProperty('shadow_texture_size'))

	def setBaked(self, mode):
		"""Set the light as baked. A baked light will only add specular highlights for objects with baked light maps"""
		self.setProperty('baked_light',mode)

	def getBaked(self):
		"""Get baked mode of light"""
		return bool(self.getProperty('baked_light'))

	def setLightTexture(self, texture):
		"""Set a texture for the light"""
		self.texture(texture, node='vizfx.light')

class VizChild(VizNode):
	"""VizChild object"""
	def save(self,filename):
		return _ipcSend(_VIZ_SAVECHILD,self.id,0,filename,0.0,0.0,0.0,0.0)

class VizGroup(VizNode):
	"""VizGroup object"""
	def save(self,filename):
		return _ipcSend(_VIZ_SAVECHILD,self.id,0,filename,0.0,0.0,0.0,0.0)

class VizTexQuad(VizNode):
	"""VizTexQuad object"""
	def save(self,filename):
		return _ipcSend(_VIZ_SAVECHILD,self.id,0,filename,0.0,0.0,0.0,0.0)

	def setSize(self, size):
		"""Set the raw (width,height) of the tex quad"""
		if _islist(size):
			self.setScale([size[0], size[1], 1.0], TEXQUAD_SIZE)
		else:
			self.setScale([size, size, 1.0], TEXQUAD_SIZE)

	def getSize(self):
		"""Get the raw (width,height) of the tex quad"""
		return self.getScale(TEXQUAD_SIZE)[:2]

class VizCustomChild(VizChild):
	"""VizCustomChild object"""
	def command(self,command, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0):
		"""Send a command to the custom  node"""
		_ipcSend(_VIZ_COMMANDCUSTOM,self.id,command,mesg,x,y,z,w)

	def get(self,*args):
		"""Retrieve data from the custom node"""
		if args:
			return VizChild.get(self,*args)
		return _ipcSend(_VIZ_GETCUSTOMDATA,self.id,0,'',0.0,0.0,0.0,0.0)

class VizText(VizNode):
	"""VizText object"""
	def setTheme(self,theme):
		"""Set the theme of the text object"""
		self.color(theme.textColor)

	def setThickness(self,thickness):
		"""Set the thickness of 3D text as a percentage of character height"""
		_ipcSend(_VIZ_TEXTSET,self.id,2,'',thickness,0.0,0.0,0.0)

	def getThickness(self):
		"""Get the thickness of 3D text as a percentage of character height"""
		return _ipcSend(_VIZ_TEXTGET,self.id,2,'',0.0,0.0,0.0,0.0)

class VizVertex(VizActor,VizCustomLinkable):
	"""Handle to an OTF vertex"""

	def __init__(self,id,parent,index):
		VizActor.__init__(self)
		VizCustomLinkable.__init__(self,id)
		self.parent = parent
		self.index = index

	def getPosition(self,mode=ABS_PARENT):
		"""Get the position of the vertex"""
		return _ipcSend(_VIZ_CHILDGET,_OTF_VERTEX,self.parent,'',self.index,mode,0.0,0.0)

	def getNormal(self,mode=ABS_PARENT):
		"""Get the normal of the vertex"""
		return _ipcSend(_VIZ_CHILDGET,_OTF_NORMAL,self.parent,'',self.index,mode,0.0,0.0)

	def getTexCoord(self,unit=0):
		"""Get the texture coordinate of the vertex"""
		return _ipcSend(_VIZ_CHILDGET,_OTF_TEXCOORD,self.parent,'',self.index,unit,0.0,0.0)

	def getVertexColor(self):
		"""Get the color of the vertex"""
		return _ipcSend(_VIZ_CHILDGET,_OTF_COLOR,self.parent,'',self.index,0.0,0.0,0.0)

	def getColor(self,node='',op=OP_DEFAULT):
		"""Get the color of the vertex"""
		return _ipcSend(_VIZ_CHILDGET,_OTF_COLOR,self.parent,'',self.index,0.0,0.0,0.0)[:3]

	def getAlpha(self,node='',op=OP_DEFAULT):
		"""Get the alpha of the vertex"""
		return _ipcSend(_VIZ_CHILDGET,_OTF_COLOR,self.parent,'',self.index,0.0,0.0,0.0)[3]

	def setPosition(self,x,y=ABS_PARENT,z=0,mode=ABS_PARENT):
		"""Modify a vertex of the On-The-Fly object"""
		if _islist(x):
			_ipcSend(_VIZ_OTFVERTEX,self.parent,self.index,'',x[0],x[1],x[2],y)
		else:
			_ipcSend(_VIZ_OTFVERTEX,self.parent,self.index,'',x,y,z,mode)

	def setNormal(self,x,y=ABS_PARENT,z=0,mode=ABS_PARENT):
		"""Modify a normal vector of the On-The-Fly object"""
		if _islist(x):
			_ipcSend(_VIZ_OTFNORMAL,self.parent,self.index,'',x[0],x[1],x[2],y)
		else:
			_ipcSend(_VIZ_OTFNORMAL,self.parent,self.index,'',x,y,z,mode)

	def setVertexColor(self,r,g=1,b=0,a=1):
		"""Modify a vertex color of an On-The-Fly object"""
		if _islist(r):
			if len(r) < 4:
				_ipcSend(_VIZ_OTFCOLOR,self.parent,self.index,'',r[0],r[1],r[2],g)
			else:
				_ipcSend(_VIZ_OTFCOLOR,self.parent,self.index,'',r[0],r[1],r[2],r[3])
		else:
			_ipcSend(_VIZ_OTFCOLOR,self.parent,self.index,'',r,g,b,a)

	def setTexCoord(self,x,y=0,z=0,unit=0):
		"""Modify a texture coordinate of the On-The-Fly object"""
		if _islist(x):
			if len(x) < 3:
				_ipcSend(_VIZ_OTFTEXCOORD,self.parent,self.index,'',x[0],x[1],0.0,unit)
			else:
				_ipcSend(_VIZ_OTFTEXCOORD,self.parent,self.index,'',x[0],x[1],x[2],unit)
		else:
			_ipcSend(_VIZ_OTFTEXCOORD,self.parent,self.index,'',x,y,z,unit)

	def setColor(self,r,g='',b=0,node='',op=OP_DEFAULT):
		"""Set the vertex color"""
		if _islist(r):
			_ipcSend(_VIZ_CHILDCOLOR,self.parent,0,str(self.index),r[0],r[1],r[2],op)
		else:
			_ipcSend(_VIZ_CHILDCOLOR,self.parent,0,str(self.index),r,g,b,op)

	def setAlpha(self,alpha,node='',op=OP_DEFAULT):
		"""Set the vertex alpha"""
		_ipcSend(_VIZ_CHILDALPHA,self.parent,0,str(self.index),alpha,op,0.0,0.0)

class VizPrimitive(VizNode):
	"""VizPrimitive object"""

	def Vertex(self,index):
		"""Return a handle to a vertex
		@return VizVertex()"""
		return VizVertex._GetObject(_ipcSend(_VIZ_CREATELINKABLE,self.id,index,'',0.0,0.0,0.0,1.0),self.id,index)

	def dynamic(self):
		"""Notify Vizard that the vertices of the object are going to be updated frequently"""
		self.disable(DISPLAY_LISTS)

	def static(self):
		"""Notify Vizard that the vertices of the object are not going to be updated frequently"""
		self.enable(DISPLAY_LISTS)

	def triangulatePolygon(self):
		"""Triangulate the last polygon layer"""
		self.enable(TRIANGULATE_POLYGON)

	def startLayer(self, type, name=''):
		"""Start a new primitive layer"""
		_ipcSend(_VIZ_STARTLAYER,type,1,name,self.id,0.0,0.0,0.0)

	def addVertex(self,x,y=0,z=0,color=None,normal=None,texCoord=None):
		"""Add a vertex to the On-The-Fly object"""
		if _islist(x):
			val = _ipcSend(_VIZ_OTFADDVERTEX,self.id,0,'',x[0],x[1],x[2],0.0)
		else:
			val = _ipcSend(_VIZ_OTFADDVERTEX,self.id,0,'',x,y,z,0.0)

		if color is not None:
			self.setVertexColor(val,color)
		if normal is not None:
			self.setNormal(val,normal)
		if texCoord is not None:
			self.setTexCoord(val,texCoord)

		return val

#	def removeVertex(self,index,count=1):
#		"""Remove 'count' vertices starting at 'index'"""
#		_ipcSend(_VIZ_OTFADDVERTEX,self.id,1,'',index,count,0.0,0.0)

	def clearVertices(self):
		"""Remove all vertices from the On-The-Fly object"""
		_ipcSend(_VIZ_OTFADDVERTEX,self.id,1,'',0,-1,0.0,0.0)

	def getVertexCount(self):
		"""Get the number of vertices"""
		return _ipcSend(_VIZ_CHILDGET,_OTF_NUMVERTS,self.id,'',0.0,0.0,0.0,0.0)

	def getVertex(self,index,mode=REL_LOCAL):
		"""Get the position of the vertex"""
		return _ipcSend(_VIZ_CHILDGET,_OTF_VERTEX,self.id,'',index,mode,0.0,0.0)

	def getNormal(self,index,mode=REL_LOCAL):
		"""Get the normal of the vertex"""
		return _ipcSend(_VIZ_CHILDGET,_OTF_NORMAL,self.id,'',index,mode,0.0,0.0)

	def getTexCoord(self,index,unit=0):
		"""Get the texture coordinate of the vertex"""
		return _ipcSend(_VIZ_CHILDGET,_OTF_TEXCOORD,self.id,'',index,unit,0.0,0.0)

	def getVertexColor(self,index):
		"""Get the color of the vertex"""
		return _ipcSend(_VIZ_CHILDGET,_OTF_COLOR,self.id,'',index,0.0,0.0,0.0)

	def setVertex(self,index,x,y=ABS_LOCAL,z=0,mode=ABS_LOCAL):
		"""Modify a vertex of the On-The-Fly object"""
		if _islist(x):
			_ipcSend(_VIZ_OTFVERTEX,self.id,index,'',x[0],x[1],x[2],y)
		else:
			_ipcSend(_VIZ_OTFVERTEX,self.id,index,'',x,y,z,mode)

	def setNormal(self,index,x,y=ABS_LOCAL,z=0,mode=ABS_LOCAL):
		"""Modify a normal vector of the On-The-Fly object"""
		if _islist(x):
			_ipcSend(_VIZ_OTFNORMAL,self.id,index,'',x[0],x[1],x[2],y)
		else:
			_ipcSend(_VIZ_OTFNORMAL,self.id,index,'',x,y,z,mode)

	def setVertexColor(self,index,r,g=1,b=0,a=1):
		"""Modify a vertex color of an On-The-Fly object"""
		if _islist(r):
			if len(r) < 4:
				_ipcSend(_VIZ_OTFCOLOR,self.id,index,'',r[0],r[1],r[2],g)
			else:
				_ipcSend(_VIZ_OTFCOLOR,self.id,index,'',r[0],r[1],r[2],r[3])
		else:
			_ipcSend(_VIZ_OTFCOLOR,self.id,index,'',r,g,b,a)

	def setTexCoord(self,index,x,y=0,z=0,unit=0):
		"""Modify a texture coordinate of the On-The-Fly object"""
		if _islist(x):
			if len(x) < 3:
				_ipcSend(_VIZ_OTFTEXCOORD,self.id,index,'',x[0],x[1],0.0,unit)
			else:
				_ipcSend(_VIZ_OTFTEXCOORD,self.id,index,'',x[0],x[1],x[2],unit)
		else:
			_ipcSend(_VIZ_OTFTEXCOORD,self.id,index,'',x,y,z,unit)

	def save(self,filename):
		"""Save object to file"""
		return _ipcSend(_VIZ_SAVECHILD,self.id,0,filename,0.0,0.0,0.0,0.0)

AVATAR_WALKSTEP = 2
AVATAR_RUNSTEP	= 4

def _IdAndName(value):
	if isinstance(value, str):
		return -1, value
	return value, ''

class VizAvatar(VizNode):
	"""VizAvatar object"""

	@classmethod
	def _OnRemoveObject(cls,obj):
		"""INTERNAL USE ONLY"""
		VizBone._RemoveAvatarBones(obj)
		VizNode._OnRemoveObject(obj)

	def __init__(self,id,**kw):
		VizNode.__init__(self,id,**kw)
		self._action = ActionController(self)
		try:
			self._action.idlepose = int(self.getConfigValue('idle_anim','1'))
		except ValueError:
			self._action.idlepose = 1
			logWarn('** WARNING: Invalid idle animation specified in avatar cfg file')
		self._face_ = None

	def lod(self,value):
		"""Set the Level-Of-Detail of the avatar"""
		_ipcSend(_VIZ_AVATARLOD,self.id,0,'',value,0.0,0.0,0.0)

	def setMorph(self,morphID,weight):
		"""Set the morph target weight for an avatar mesh"""
		id, name = _IdAndName(morphID)
		_ipcSend(_VIZ_AVATARMORPH,self.id,0,name,id,weight,0.0,0.0)
	morph = DeprecateObject(setMorph) #To be compatible with face objects

	def clearMorph(self):
		"""Clear the morph targets from the avatar"""
		_ipcSend(_VIZ_AVATARMORPH,self.id,1,'',0.0,0.0,0.0,0.0)

	def getMorph(self,morphID):
		"""Get the morph target weight for an avatar mesh"""
		id, name = _IdAndName(morphID)
		return _ipcSend(_VIZ_CHILDGET,_MESH_MORPH,self.id,name,id,0.0,0.0,0.0)

	def getMorphID(self,name):
		"""Get the ID of a morph target from the name"""
		return _ipcSend(_VIZ_CHILDGET,_MESH_MORPH_ID,self.id,name,0.0,0.0,0.0,0.0)

	def getMorphList(self):
		"""Return a list of morph names for the specified mesh"""
		return _ipcSend(_VIZ_CHILDGET,_MESH_MORPH_NAMES,self.id,'',0.0,0.0,0.0,0.0)

	def speed(self,value):
		"""Set the speed of the avatar"""
		_ipcSend(_VIZ_AVATARSPEED,self.id,-1,'',value,0.0,0.0,0.0)
		self._action.speed = value

	def setUpdateRate(self,rate):
		"""Set the update rate of the avatar"""
		_ipcSend(_VIZ_AVATARRATE,self.id,0,'',rate,0.0,0.0,0.0)
	updaterate = DeprecateObject(setUpdateRate)

	def execute(self, animation, delay_in=AVATAR_DELAY, delay_out=AVATAR_DELAY, freeze=False, weight=1.0, begin=0.0, end=-1.0):
		"""Execute an animation once"""
		id, name = _IdAndName(animation)
		_ipcSend(_VIZ_AVATAREXECUTE,0,0,'',weight,begin,end,0.0)
		_ipcSend(_VIZ_AVATAREXECUTE,self.id,id,name,delay_in,delay_out,freeze,1.0)

	def blend(self,animation,weight,delay=AVATAR_DELAY):
		"""Blend an animation into the current animations"""
		id, name = _IdAndName(animation)
		_ipcSend(_VIZ_AVATARBLEND,self.id,id,name,weight,delay,0.0,0.0)

	def state(self,animation,delay=AVATAR_DELAY):
		"""Set the given animation of the avatar"""
		id, name = _IdAndName(animation)
		_ipcSend(_VIZ_AVATARSTATE,self.id,id,name,delay,0.0,0.0,0.0)

	def forceAnimationLoad(self, animation):
		"""Force a delay-loaded animation to load now"""
		id, name = _IdAndName(animation)
		return _ipcSend(_VIZ_AVATARCLEAR,self.id,id,name,0.0,0.0,0.0,3.0)

	def stopAnimation(self,animation,delay=AVATAR_DELAY):
		"""Clear the animation from the avatar"""
		id, name = _IdAndName(animation)
		_ipcSend(_VIZ_AVATARCLEAR,self.id,id,name,delay,0.0,0.0,0.0)

	def stopCycle(self,animation,delay=AVATAR_DELAY):
		"""Clear the animation from the avatars cycle"""
		id, name = _IdAndName(animation)
		_ipcSend(_VIZ_AVATARCLEAR,self.id,id,name,delay,0.0,0.0,1.0)

	def stopAction(self,animation,delay=AVATAR_DELAY):
		"""Clear the animation from the avatars actions"""
		id, name = _IdAndName(animation)
		_ipcSend(_VIZ_AVATARCLEAR,self.id,id,name,delay,0.0,0.0,2.0)

	def setAnimationSpeed(self,animation,factor):
		"""Set the animation speed of the avatar"""
		id, name = _IdAndName(animation)
		_ipcSend(_VIZ_AVATARSPEED,self.id,id,name,factor,0.0,0.0,0.0)

	def getAnimationSpeed(self,animation):
		"""Return speed of the animation"""
		id, name = _IdAndName(animation)
		return _ipcSend(_VIZ_CHILDGET,_ANIMATION_SPEED,self.id,name,id,0.0,0.0,0.0)

	def setAnimationTime(self,animation,time):
		"""Set the elapsed time for an animation"""
		id, name = _IdAndName(animation)
		_ipcSend(_VIZ_AVATARSETTIME,self.id,id,name,time,0.0,0.0,0.0)

	def getAnimationTime(self,animation):
		"""Get current time of the animation"""
		id, name = _IdAndName(animation)
		return _ipcSend(_VIZ_CHILDGET,_ANIMATION_TIME,self.id,name,id,0.0,0.0,0.0)

	def getActionRunning(self,animation):
		"""Returns if the animation action is running"""
		id, name = _IdAndName(animation)
		return _ipcSend(_VIZ_CHILDGET,_AVATAR_ACTION_RUNNING,self.id,name,id,0.0,0.0,0.0)

	def getCycleRunning(self,animation):
		"""Returns if the animation cycle is running"""
		id, name = _IdAndName(animation)
		return _ipcSend(_VIZ_CHILDGET,_AVATAR_CYCLE_RUNNING,self.id,name,id,0.0,0.0,0.0)

	def getDuration(self,animation):
		"""Get the duration of an animation"""
		id, name = _IdAndName(animation)
		return _ipcSend(_VIZ_CHILDGET,_ANIMATION_DURATION,self.id,name,id,0.0,0.0,0.0)

	def getAnimationID(self,name):
		"""Get the animation number given the name"""
		return _ipcSend(_VIZ_CHILDGET,ANIMATION,self.id,name,0.0,0.0,0.0,0.0)

	def getAnimationList(self):
		"""Get list of animations available on avatar"""
		return _ipcSend(_VIZ_CHILDGET,_ANIMATION_NAMES,self.id,'',0.0,0.0,0.0,0.0)

	def getMeshID(self,name):
		"""Get the mesh number given the name"""
		return _ipcSend(_VIZ_CHILDGET,_MESH_BY_NAME,self.id,name,0.0,0.0,0.0,0.0)

	def getMeshList(self):
		"""Get list of meshes available on avatar"""
		return _ipcSend(_VIZ_CHILDGET,_MESH_NAMES,self.id,'',0.0,0.0,0.0,0.0)

	def getConfigValue(self,name,default=''):
		"""Get a value from the avatars cfg file"""
		val = _ipcSend(_VIZ_CHILDGET,_AVATAR_VARIABLE,self.id,name,0.0,0.0,0.0,0.0)
		if val is None:
			return default
		return val

	def getBoneList(self):
		"""Get list of bones available on avatar"""
		val = _ipcSend(_VIZ_CHILDGET,_BONE_LIST,self.id,'',0.0,0.0,0.0,0.0)
		return [ VizBone._GetObject(id) for id in val ]

	def getRootBoneList(self):
		"""Get list of root bones available on avatar"""
		val = _ipcSend(_VIZ_CHILDGET,_BONE_LIST,self.id,'',1.0,0.0,0.0,0.0)
		return [ VizBone._GetObject(id) for id in val ]

	def getBone(self,name):
		"""Get the bone with the given name
		@return VizBone()"""
		return VizBone._GetObject(_ipcSend(_VIZ_GETAVATARBONE,self.id,0,name,0.0,0.0,0.0,0.0))

	def face(self,obj,head=None,clamp=None):
		"""Attatch a face object to the head"""
		if isinstance(obj,str):
			newface = addFace(obj)
			if newface.valid():
				self.setFace(newface,head,clamp)
				return newface
			else:
				return None
		self.setFace(obj,head,clamp)

	def setFace(self,face,head=None,clamp=None):
		"""Attach a face object to the avatars head"""
		if self._face_:
			#Remove existing face
			_ipcSend(_VIZ_UNLINKFACE,self._face_.id,0,'',0.0,0.0,0.0,0.0)
			head_mesh = self.getConfigValue('head_mesh')
			if head_mesh:
				self.visible(1,head_mesh)
			self._face_ = None

		if isinstance(face,VizFace):
			#Set new face
			if clamp is None:
				clamp = self.getConfigValue('neck_bone','skel_Neck')
			if head is None:
				head = self.getConfigValue('head_bone','skel_Head')
			headBone = self.getBone(head)
			clampBone = self.getBone(clamp)
			_ipcSend(_VIZ_LINKFACEAVATAR,face.id,headBone.id,'',clampBone.id,0.0,0.0,0.0)
			head_mesh = self.getConfigValue('head_mesh')
			if head_mesh:
				self.visible(0,head_mesh)
			self._face_ = face

	def getFace(self):
		"""Return the current face object of the avatar"""
		return self._face_

	def idlepose(self,pose):
		"""Set the idle pose of the avatar"""
		self._action.idlepose = pose

class VizBone(VizObject):
	"""VizBone object"""

	_VizObjectCache = {}
	_VizLinkableType = _VIZ_BONE_LINKABLE

	@classmethod
	def _RemoveAvatarBones(cls,obj):
		"""INTERNAL USE ONLY"""
		if obj.valid():
			begin = obj.id * 256
			end = begin + 256
			bones = [ id for id in cls._VizObjectCache.keys() if begin <= id < end ]
			for id in bones:
				cls._RemoveObject(id)

	def __init__(self, id):
		VizObject.__init__(self, id)

	def lock(self, recurse = 0):
		"""Lock the bone in place"""
		_ipcSend(_VIZ_LOCKBONE,self.id,1,'',recurse,0.0,0.0,0.0)

	def unlock(self, recurse = 0):
		"""Unlock the bone"""
		_ipcSend(_VIZ_LOCKBONE,self.id,0,'',recurse,0.0,0.0,0.0)

	def setPosition(self,x,y=ABS_PARENT,z=0,mode=ABS_PARENT):
		"""Translate the bone"""
		if _islist(x):
			_ipcSend(_VIZ_TRANSLATEBONE,self.id,y,'',x[0],x[1],x[2],0.0)
		else:
			_ipcSend(_VIZ_TRANSLATEBONE,self.id,mode,'',x,y,z,0.0)

	def offset(self,x,y=0,z=0):
		"""Set the offset for bone translations"""
		if _islist(x):
			_ipcSend(_VIZ_OFFSETBONE,self.id,0,'',x[0],x[1],x[2],0.0)
		else:
			_ipcSend(_VIZ_OFFSETBONE,self.id,0,'',x,y,z,0.0)

	def setEuler(self, x, y=ABS_PARENT, z=0, mode=ABS_PARENT):
		"""Set euler of bone"""
		if _islist(x):
			_ipcSend(_VIZ_ROTEULERBONE,self.id,y,'',x[0],x[1],x[2],0.0)
		else:
			_ipcSend(_VIZ_ROTEULERBONE,self.id,mode,'',x,y,z,0.0)

	def setAxisAngle(self, x, y=ABS_PARENT, z=0, deg=0, mode=ABS_PARENT):
		"""Set axis angle of bone"""
		if _islist(x):
			_ipcSend(_VIZ_ROTAXISBONE,self.id,y,'',x[0],x[1],x[2],x[3])
		else:
			_ipcSend(_VIZ_ROTAXISBONE,self.id,mode,'',x,y,z,deg)

	def setQuat(self, x, y=ABS_PARENT, z=0, w=0, mode=ABS_PARENT):
		"""Set quaternion of bone"""
		if _islist(x):
			_ipcSend(_VIZ_ROTQUATBONE,self.id,y,'',x[0],x[1],x[2],x[3])
		else:
			_ipcSend(_VIZ_ROTQUATBONE,self.id,mode,'',x,y,z,w)

	@DeprecateObject
	def lookat(self,x, y=0, z=ABSOLUTE, roll=0, mode=ABSOLUTE):
		"""Make the bone face the given point"""
		if _islist(x):
			_ipcSend(_VIZ_BONELOOK,self.id,z,'',x[0],x[1],x[2],y)
		else:
			_ipcSend(_VIZ_BONELOOK,self.id,mode,'',x,y,z,roll)

	def lookAt(self, point, roll=0.0, mode=ABS_PARENT):
		"""Set the rotation of the bone to look at the specified point"""
		_ipcSend(_VIZ_BONELOOK,self.id,mode,'',point[0],point[1],point[2],roll)

	def setMatrix(self,transform,mode=ABS_PARENT):
		"""Set the 4x4 matrix of the bone"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', transform[0], transform[1], transform[2], transform[3])
		_ipcSend(_VIZ_SETMATRIX2, 0, 0, '', transform[4], transform[5], transform[6], transform[7])
		_ipcSend(_VIZ_SETMATRIX3, 0, 0, '', transform[8], transform[9], transform[10], transform[11])
		_ipcSend(_VIZ_SETMATRIX4, 0, 0, '', transform[12], transform[13], transform[14], transform[15])
		_ipcSend(_VIZ_SETBONEMAT,self.id,mode,'',0.0,0.0,0.0,0.0)

	def resetMatrix(self, mask=LINK_ALL, mode=ABS_PARENT):
		"""Reset transform matrix of bone"""
		_ipcSend(_VIZ_LINKABLESET,self.id,_CLEAR_MASK,'',self._VizLinkableType,mask,mode,0.0)

	def getAvatar(self):
		""""Return the avatar that the bone is a part of
		@return VizAvatar()"""
		return _GetNode(_ipcSend(_VIZ_GETBONEINFO,_BONE_AVATAR,self.id,'',0.0,0.0,0.0,0.0))

	def getParent(self):
		"""Return parent bone.
		@return VizBone()"""
		return VizBone._GetObject(_ipcSend(_VIZ_GETBONEINFO,PARENTS,self.id,'',0.0,0.0,0.0,0.0))

	def getChildren(self):
		"""Return tuple containing all children bones"""
		val = _ipcSend(_VIZ_GETBONEINFO,CHILDREN,self.id,'',0.0,0.0,0.0,0.0)
		return [ VizBone._GetObject(id) for id in val ]

	def getName(self):
		"""Return name of bone"""
		return _ipcSend(_VIZ_GETBONEINFO,FILENAME,self.id,'',0.0,0.0,0.0,0.0)

	def getPosition(self, mode = ABS_PARENT):
		"""Get position of bone"""
		return _ipcSend(_VIZ_GETBONEINFO,POSITION,self.id,'',mode,0.0,0.0,0.0)

	def getEuler(self, mode = ABS_PARENT):
		"""Get euler angle of bone"""
		return _ipcSend(_VIZ_GETBONEINFO,EULER,self.id,'',mode,0.0,0.0,0.0)

	def getAxisAngle(self, mode = ABS_PARENT):
		"""Get axis angle of bone"""
		return _ipcSend(_VIZ_GETBONEINFO,AXISANGLE,self.id,'',mode,0.0,0.0,0.0)

	def getQuat(self, mode = ABS_PARENT):
		"""Get quaternion of bone"""
		return _ipcSend(_VIZ_GETBONEINFO,QUAT,self.id,'',mode,0.0,0.0,0.0)

	def getMatrix(self, mode = ABS_PARENT):
		"""Get matrix of bone"""
		return Transform(_ipcSend(_VIZ_GETBONEINFO,MATRIX,self.id,'',mode,0.0,0.0,0.0))

	def getLineForward(self, mode=ABS_PARENT, length=1.0):
		"""Return Line object starting at linkable position and ending at specified length along forward vector"""
		return Line(_ipcSend(_VIZ_LINKABLE_GET,LOOK,self.id,'',self._VizLinkableType,mode,length,0.0))

class VizFace(VizNode):
	"""VizFace object"""
	def setMorph(self,target,percent):
		"""Set the morph target percent value"""
		_ipcSend(_VIZ_FACEMORPH,self.id,target,'',percent,0.0,0.0,0.0)

	def getmorph(self,target):
		"""Get the morph target percent value"""
		if isinstance(target,str):
			return self.getMorphID(target)

		return self.getMorph(target)

	def clearMorph(self):
		"""Clear all morph targets from face"""
		_ipcSend(_VIZ_CLEARMORPH,self.id,0,'',0.0,0.0,0.0,0.0)

	def getMorph(self,target):
		"""Get the current morph target value"""
		return _ipcSend(_VIZ_CHILDGET,_MORPH_VALUE,self.id,'',target,0.0,0.0,0.0)

	def getMorphID(self,name):
		"""Get the ID of a morph target from the name"""
		return _ipcSend(_VIZ_CHILDGET,_MORPH_ID,self.id,name,0.0,0.0,0.0,0.0)

	def getMorphList(self):
		"""Get a list of all the morph target names"""
		return _ipcSend(_VIZ_CHILDGET,_MORPH_NAMES,self.id,'',0.0,0.0,0.0,0.0)

	def getGeomList(self):
		"""Get a list of all the geom names"""
		return _ipcSend(_VIZ_CHILDGET,_FACEGEOM_NAMES,self.id,'',0.0,0.0,0.0,0.0)

class VizGUICanvas(VizNode):
	"""VizGUICanvas object"""

	def setRenderWorldOverlay(self, resolution, fov, distance, scene=MainScene):
		"""Set canvas to render over the world at the specified 'resolution'.
		Canvas will be projected at the vertical 'fov' to a 'distance' in front of the view"""
		_ipcSend(_VIZ_GUICANVASSET, 1, self.id, '', resolution[0], resolution[1], fov, distance)
		if scene:
			self.setParent(WORLD, scene)

	def setRenderWorld(self, resolution, size, scene=MainScene):
		"""Set canvas to render within the world at the specified 'resolution'.
		Canvas will be scaled to specified world coordinate 'size'."""
		_ipcSend(_VIZ_GUICANVASSET, 2, self.id, '', resolution[0], resolution[1], size[0], size[1])
		if scene:
			self.setParent(WORLD, scene)

	def setRenderScreenOrtho(self, window=MainWindow):
		"""Set canvas to render in orthographic mode on top of the screen"""
		window_id = window.id if window else -1
		_ipcSend(_VIZ_GUICANVASSET, 3, self.id, '', window_id, 0.0, 0.0, 0.0)

	def setRenderScreenPerspective(self, fov, window=MainWindow):
		"""Set canvas to render at the specified vertical 'fov' on top of the screen"""
		window_id = window.id if window else -1
		_ipcSend(_VIZ_GUICANVASSET, 4, self.id, '', fov, window_id, 0.0, 0.0)

	def getRenderMode(self):
		"""Get the canvas render mode"""
		return _ipcSend(_VIZ_GUICANVASGET, 1, self.id, '', 0.0, 0.0, 0.0, 0.0)

	def setRenderResolution(self, size):
		"""Set [width, height] render resolution of canvas"""
		self.setScale([size[0], size[1], 1.0], CANVAS_RESOLUTION)

	def getRenderResolution(self):
		"""Get [width, height] render resolution of canvas"""
		return self.getScale(CANVAS_RESOLUTION)[:2]

	def setCursorVisible(self, mode):
		"""Set visibility of canvas cursor"""
		self.visible(mode, CANVAS_CURSOR)

	def getCursorVisible(self):
		"""Get visibility of canvas cursor"""
		return self.getVisible(CANVAS_CURSOR)

	def setCursorAlignment(self, mode):
		"""Set alignment of cursor quad"""
		self.alignment(mode, CANVAS_CURSOR)

	def getCursorAlignment(self):
		"""Get alignment of cursor quad"""
		return self.getAlignment(CANVAS_CURSOR)

	def setCursorMoveScale(self, scale):
		"""Set scale factor for translating mouse to cursor movement"""
		self.setScale([scale, 1.0, 1.0], CANVAS_CURSOR_PIXELS)

	def getCursorMoveScale(self):
		"""Get scale factor for translating mouse to cursor movement"""
		return self.getScale(CANVAS_CURSOR_PIXELS)[0]

	def setCursorPosition(self, pos, mode=CANVAS_CURSOR_NORMALIZED):
		"""Set [x,y] position of canvas cursor"""
		self.setPosition([pos[0], pos[1], 0.0], mode)

	def getCursorPosition(self, mode=CANVAS_CURSOR_NORMALIZED):
		"""Get [x,y] position of canvas cursor"""
		return self.getPosition(mode)[:2]

	def setCursorSize(self, size):
		"""Set [width, height] size of canvas cursor"""
		self.setScale([size[0], size[1], 1.0], CANVAS_CURSOR_SIZE)

	def getCursorSize(self):
		"""Get [width, height] size of canvas cursor"""
		return self.getScale(CANVAS_CURSOR_SIZE)[:2]

	def setMouseStyle(self, style, mode=MASK_SET):
		"""Set canvas mouse style flags"""
		_ipcSend(_VIZ_GUICANVASSET, 5, self.id, '', style, mode, 0.0, 0.0)

	def getMouseStyle(self):
		"""Get canvas mouse style flags"""
		return _ipcSend(_VIZ_GUICANVASGET, 5, self.id, '', 0.0, 0.0, 0.0, 0.0)

	def sendMouseButtonEvent(self, button, state):
		"""Simulate a mouse button event on the canvas"""
		return _ipcSend(_VIZ_GUICANVASSET, 6, self.id, '', button, state, 0.0, 0.0)

	def pick(self, info = False, pos = None, mode=CANVAS_CURSOR_NORMALIZED, all = False, ignoreBackFace=False, computePath=False, ignoreClipped=False):
		"""Performs a pick test on the canvas"""

		flag = 0
		if pos is None:
			pos = self.getCursorPosition(mode)
		if not all:
			flag |= _INTERSECT_NEAREST
		if ignoreBackFace:
			flag |= _INTERSECT_IGNORE_BACK_FACE
		if computePath and info:
			flag |= _INTERSECT_COMPUTE_PATH
		if ignoreClipped:
			flag |= _INTERSECT_IGNORE_CLIPPED

		if info:
			return _ipcSend(_VIZ_GUICANVASGET, 7, self.id, '', pos[0], pos[1], mode, flag)
		else:
			return _ipcSend(_VIZ_GUICANVASGET, 6, self.id, '', pos[0], pos[1], mode, flag)

	def lineToCursor(self, line, mode=CANVAS_CURSOR_NORMALIZED, apply=True):
		"""Intersects the given line in world coordinates with the canvas plane and returns the [x,y] cursor position"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', line[0], line[1], line[2], 0.0)
		_ipcSend(_VIZ_SETMATRIX2, 0, 0, '', line[3], line[4], line[5], 0.0)
		return _ipcSend(_VIZ_GUICANVASGET, 8, self.id, '', mode, apply, 0, 0)

class VizGUIObject(VizNode):
	"""VizGUI object"""
	def enable(self,*args,**kw):
		"""Enable interaction with the GUI object"""
		if args:
			VizNode.enable(self,*args,**kw)
		else:
			_ipcSend(_VIZ_GUIENABLE,self.id,1,'',0.0,0.0,0.0,0.0)

	def disable(self,*args,**kw):
		"""Disable interaction with the GUI object"""
		if args:
			VizNode.disable(self,*args,**kw)
		else:
			_ipcSend(_VIZ_GUIENABLE,self.id,0,'',0.0,0.0,0.0,0.0)

	def setEnabled(self, mode):
		"""Set enabled state of GUI object"""
		_ipcSend(_VIZ_GUIENABLE,self.id,mode,'',0.0,0.0,0.0,0.0)

	def getEnabled(self):
		"""Return whether the GUI object is enabled"""
		return _ipcSend(_VIZ_CHILDGET,114,self.id,'',0.0,0.0,0.0,0.0)

	def setFocus(self,val):
		"""Set input focus for the GUI object"""
		_ipcSend(_VIZ_FOCUSNODE,self.id,val,'',0.0,0.0,0.0,0.0)

	def getFocus(self):
		"""Returns whether the item has input focus"""
		return _ipcSend(_VIZ_CHILDGET,_FOCUS,self.id,'',0.0,0.0,0.0,0.0)

	def getHover(self):
		"""Returns whether the item is currently being hovered by the cursor"""
		return _ipcSend(_VIZ_CHILDGET,129,self.id,'',0.0,0.0,0.0,0.0)

	def getLength(self):
		"""Returns the length of the GUI object"""
		return _ipcSend(_VIZ_CHILDGET,LENGTH,self.id,'',0.0,0.0,0.0,0.0)

	def setLength(self,val):
		"""Set the length of the GUI object"""
		_ipcSend(_VIZ_GUISETLENGTH,self.id,0,'',val,0.0,0.0,0.0)

	def setTheme(self,theme):
		"""Set the theme of the GUI object"""
		setTheme(theme,node=self)

class VizCheckBox(VizGUIObject):
	"""VizButton object"""
	def downpicture(self, filename):
		"""Set the picture when the Button is down"""
		_ipcSend(_VIZ_CHECKPIC,self.id,0,filename,0.0,0.0,0.0,0.0)

	def uppicture(self, filename):
		"""Set the picture when the Button is up"""
		_ipcSend(_VIZ_UNCHECKPIC,self.id,0,filename,0.0,0.0,0.0,0.0)

	def get(self,*args):
		"""Get whether the button is down or up"""
		if args:
			return VizNode.get(self,*args)
		return _ipcSend(_VIZ_GETCHECK,self.id,0,'',0.0,0.0,0.0,0.0)

	def set(self,state):
		"""Set whether the button is down or up"""
		_ipcSend(_VIZ_SETCHECK,self.id,state,'',0.0,0.0,0.0,0.0)

class VizRadioButton(VizCheckBox):
	"""VizRadioButton object"""
	def getGroupName(self): return self.getFilename()
	def getGroup(self): return RadioGroup(self.getFilename())

class VizSlider(VizGUIObject):
	"""VizSlider object"""
	def set(self,pos):
		"""Set the position of the slider tick, 0 to 1"""
		_ipcSend(_VIZ_SETTICKPOS,self.id,0,'',pos,0.0,0.0,0.0)

	def setTickSize(self,x,y=0):
		"""Set the size of the tick"""
		if _islist(x):
			_ipcSend(_VIZ_SETTICKSIZE,self.id,0,'',x[0],x[1],0.0,0.0)
		else:
			_ipcSend(_VIZ_SETTICKSIZE,self.id,0,'',x,y,0.0,0.0)

	def get(self,*args):
		"""Get the position of the slider tick, 0 to 1"""
		if args:
			return VizNode.get(self,*args)
		return _ipcSend(_VIZ_GETTICKPOS,self.id,0,'',0.0,0.0,0.0,0.0)

	def tickpicture(self,filename):
		"""Set the picture for the tick"""
		_ipcSend(_VIZ_SLIDERTICKPIC,self.id,0,filename,0.0,0.0,0.0,0.0)

	def barpicture(self,filename):
		"""Set the picture for the bar"""
		_ipcSend(_VIZ_SLIDERBACKPIC,self.id,0,filename,0.0,0.0,0.0,0.0)

	def vertical(self):
		"""Make the slider vertical"""
		self.setAxisAngle(0,0,1,90)

	def horizontal(self):
		"""Make the slider horizontal"""
		self.setAxisAngle(0,0,1,0)

	def margin(self,val):
		"""Set the margin of the slider tick"""
		_ipcSend(_VIZ_SLIDERMARGIN,self.id,0,'',val,0.0,0.0,0.0)

	def dragging(self):
		"""Returns whether the slider is being dragged"""
		return _ipcSend(_VIZ_SLIDERDRAGGING,self.id,0,'',0.0,0.0,0.0,0.0)

class VizTextbox(VizGUIObject):
	"""VizTextbox object"""
	def get(self,*args):
		"""Get the text of the textbox"""
		if args:
			return VizNode.get(self,*args)
		return self.getMessage()

	def setCursorPos(self,pos):
		"""Set the position of the cursor in the textbox"""
		_ipcSend(_VIZ_SETCURSORPOS,self.id,pos,'',0.0,0.0,0.0,0.0)

	def getCursorPos(self):
		"""Get the position of the cursor"""
		return _ipcSend(_VIZ_CHILDGET,_CURSOR_POS,self.id,'',0.0,0.0,0.0,0.0)

	def overflow(self,mode):
		"""Set the overflow mode for the textbox"""
		_ipcSend(_VIZ_OVERFLOWMODE,self.id,mode,'',0.0,0.0,0.0,0.0)

class VizProgressBar(VizGUIObject):
	"""VizProgressBar object"""
	def set(self,val):
		"""Set the percentage of the progress bar"""
		_ipcSend(_VIZ_PROGRESSSET,self.id,0,'',val,0.0,0.0,0.0)

	def get(self,*args):
		"""Get the percentage of the progress bar"""
		if args:
			return VizNode.get(self,*args)
		return _ipcSend(_VIZ_PROGRESSGET,self.id,0,'',0.0,0.0,0.0,0.0)

class VizButtonLabel(VizGUIObject):
	"""VizButtonLabel object"""
	def get(self,*args):
		"""Get whether the button is down or up"""
		if args:
			return VizNode.get(self,*args)
		return _ipcSend(_VIZ_GETCHECK,self.id,0,'',0.0,0.0,0.0,0.0)

	def set(self, state):
		"""Set whether the button is down or up"""
		_ipcSend(_VIZ_SETCHECK,self.id,state,'',0.0,0.0,0.0,0.0)

	def overflow(self,mode):
		"""Set the overflow mode for the button label"""
		_ipcSend(_VIZ_OVERFLOWMODE,self.id,mode,'',0.0,0.0,0.0,0.0)

	def getGroupName(self):
		"""Return group name if button is assigned to a group"""
		return self.getFilename()

	def getGroup(self):
		"""Return radio group if button is assigned to a group"""
		return RadioGroup(self.getFilename())

class VizDropList(VizGUIObject):
	"""VizDropList object"""
	def __init__(self,id,options=None,items=None,**kw):
		VizGUIObject.__init__(self,id,**kw)

		if self.valid():
			if options is not None:
				self.addItems(options)
			if items is not None:
				self.addItems(items)

	def addItem(self,text,index=-1):
		"""Add an item to the drop list"""
		_ipcSend(_VIZ_DROPLISTMODIFY,self.id,0,text,index,0.0,0.0,0.0)

	def addItems(self,items):
		"""Add all the items in the list to the drop list"""
		for item in items:
			self.addItem(item)

	def getItem(self,index):
		"""Get the text of the specified item"""
		return _ipcSend(_VIZ_CHILDGET,_ITEM_TEXT,self.id,'',index,0.0,0.0,0.0)

	def getItems(self):
		"""Get a list of all the items"""
		return [ self.getItem(x) for x in range(self.getItemCount()) ]

	def getItemCount(self):
		"""Get number of items in droplist"""
		return _ipcSend(_VIZ_CHILDGET,_ITEM_COUNT,self.id,'',0.0,0.0,0.0,0.0)

	def getSelection(self):
		"""Get selected item index"""
		return _ipcSend(_VIZ_CHILDGET,_SELECTION,self.id,'',0.0,0.0,0.0,0.0)

	def removeItem(self,index):
		"""Remove an item from the drop list"""
		_ipcSend(_VIZ_DROPLISTMODIFY,self.id,1,'',index,0.0,0.0,0.0)

	def clearItems(self):
		"""Remove all items from the drop list"""
		for x in range(self.getItemCount()):
			self.removeItem(0)

	def select(self,index):
		"""Set the selection of the drop list"""
		_ipcSend(_VIZ_DROPLISTMODIFY,self.id,2,'',index,0.0,0.0,0.0)

	def overflow(self,mode):
		"""Set the overflow mode for the drop list"""
		_ipcSend(_VIZ_OVERFLOWMODE,self.id,mode,'',0.0,0.0,0.0,0.0)

class VizTabGroup(VizDropList):
	"""VizTabGroup object"""

	def __init__(self, id, vertical=None, **kw):
		VizDropList.__init__(self, id, **kw)

		if self.valid():
			if vertical is not None:
				self.setVerticalLayout(vertical)

	def setVerticalLayout(self, mode):
		"""Set vertical layout for tab group"""
		self.setProperty('vertical',mode)

	def getVerticalLayout(self):
		"""Get vertical layout mode of tab group"""
		return bool(self.getProperty('vertical'))

class VizRenderNode(VizNode):
	"""VizRenderNode object"""
	def __init__(self,id,buffer=None,clearMask=None,size=None,inheritView=None,autoClip=None,**kw):
		VizNode.__init__(self,id,**kw)

		self._viewportLink = None

		if self.valid():
			if buffer is not None:
				self.setBuffer(buffer)
			if clearMask is not None:
				self.setClearMask(clearMask)
			if size is not None:
				self.setSize(size[0],size[1])
			if inheritView is not None:
				self.setInheritView(inheritView)
			if autoClip is not None:
				self.setAutoClip(autoClip)

	def setScene(self, scene, clear=False):
		"""Set the scene to render"""
		if not scene:
			scene = -1
		_ipcSend(_VIZ_RENDERNODESET,5,self.id,'',_sceneID(scene),clear,0.0,0.0)

	def getScene(self):
		"""Get render node scene"""
		return _ipcSend(_VIZ_RENDERNODEGET,self.id,5,'',0.0,0.0,0.0,0.0)

	def setBuffer(self,buffer):
		"""Set buffer to render to"""
		_ipcSend(_VIZ_RENDERNODESET,0,self.id,'',buffer,0.0,0.0,0.0)

	def getBuffer(self):
		"""Get target render buffer"""
		return _ipcSend(_VIZ_RENDERNODEGET,self.id,0,'',0.0,0.0,0.0,0.0)

	def setImplicitBufferMask(self, mask, mode=MASK_SET):
		"""Set the implicit buffer mask of render node"""
		_ipcSend(_VIZ_RENDERNODESET,18,self.id,'',mask,mode,0.0,0.0)

	def getImplicitBufferMask(self):
		"""Get the implicit buffer mask of render node"""
		return _ipcSend(_VIZ_RENDERNODEGET,self.id,18,'',0.0,0.0,0.0,0.0)

	def setClearMask(self,mask, mode=MASK_SET):
		"""Set clear mask of render node"""
		_ipcSend(_VIZ_RENDERNODESET,1,self.id,'',mask,mode,0.0,0.0)

	def getClearMask(self):
		"""Get clear mask of render node"""
		return _ipcSend(_VIZ_RENDERNODEGET,self.id,1,'',0.0,0.0,0.0,0.0)

	def setClearColor(self,color):
		"""Set clear color of render node"""
		if color is None:
			_ipcSend(_VIZ_RENDERNODESET,9,self.id,'',-1,-1,-1,0.0)
		elif len(color) >= 4:
			_ipcSend(_VIZ_RENDERNODESET,9,self.id,'',color[0],color[1],color[2],color[3])
		else:
			_ipcSend(_VIZ_RENDERNODESET,9,self.id,'',color[0],color[1],color[2],1.0)

	def getClearColor(self):
		"""Get clear color of render node"""
		return _ipcSend(_VIZ_RENDERNODEGET,self.id,9,'',0.0,0.0,0.0,0.0)

	def setSize(self,width,height,x=0,y=0):
		"""Set resolution of render node"""
		_ipcSend(_VIZ_RENDERNODESET,2,self.id,'',x,y,width,height)

	def setViewport(self,viewport):
		"""Set viewport of render node"""
		if viewport is None:
			_ipcSend(_VIZ_RENDERNODESET,2,self.id,'',-1.0,-1.0,-1.0,-1.0)
		else:
			_ipcSend(_VIZ_RENDERNODESET,2,self.id,'',viewport[0],viewport[1],viewport[2],viewport[3])

	def getViewport(self):
		"""Get viewport of render node"""
		return _ipcSend(_VIZ_RENDERNODEGET,self.id,2,'',0.0,0.0,0.0,0.0)

	def setOrder(self,mode=PRE_RENDER,order=0):
		"""Set render order of render node"""
		_ipcSend(_VIZ_RENDERNODESET,12,self.id,'',mode,order,0.0,0.0)

	def getOrderMode(self):
		"""Get render order mode"""
		return _ipcSend(_VIZ_RENDERNODEGET,self.id,12,'',0.0,0.0,0.0,0.0)

	def getOrderNum(self):
		"""Get render order num"""
		return _ipcSend(_VIZ_RENDERNODEGET,self.id,13,'',0.0,0.0,0.0,0.0)

	def setHUD(self, left, right, bottom, top, renderQuad=False):
		"""Setup the render node as a HUD"""
		if renderQuad:
			_ipcSend(_VIZ_RENDERNODESET,8,self.id,'',left,right,bottom,top)
		else:
			_ipcSend(_VIZ_RENDERNODESET,7,self.id,'',left,right,bottom,top)

	def setFov(self, vert, ratio, near, far):
		"""Set perspective matrix for render node"""
		self.setProjectionMatrix(Matrix.perspective(vert, ratio, near, far))

	def setProjectionMatrix(self, mat):
		"""Set projection matrix of render node"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', mat[0], mat[1], mat[2], mat[3])
		_ipcSend(_VIZ_SETMATRIX2, 0, 0, '', mat[4], mat[5], mat[6], mat[7])
		_ipcSend(_VIZ_SETMATRIX3, 0, 0, '', mat[8], mat[9], mat[10], mat[11])
		_ipcSend(_VIZ_SETMATRIX4, 0, 0, '', mat[12], mat[13], mat[14], mat[15])
		_ipcSend(_VIZ_RENDERNODESET,4,self.id,'',0.0,0.0,0.0,0.0)

	def getProjectionMatrix(self):
		"""Get projection matrix of render node"""
		return Transform(_ipcSend(_VIZ_RENDERNODEGET,self.id,4,'',0.0,0.0,0.0,0.0))

	def setInheritView(self, inherit, mode=PRE_MULT):
		"""Set if the render node should inherit view/projection matrix from camera"""
		_ipcSend(_VIZ_RENDERNODESET,6,self.id,'',inherit,mode,0.0,0.0)

	def getInheritView(self):
		"""Get whether view/projection matrix is inherited"""
		return _ipcSend(_VIZ_RENDERNODEGET,self.id,6,'',0.0,0.0,0.0,0.0)

	def getInheritViewMultOrder(self):
		"""Get matrix multiplication order for inherited view"""
		return _ipcSend(_VIZ_RENDERNODEGET,self.id,7,'',0.0,0.0,0.0,0.0)

	def setAutoClip(self, autoClip, maxFarPlane=AUTO_COMPUTE):
		"""Set whether clip planes will be auto computed"""
		_ipcSend(_VIZ_RENDERNODESET,10,self.id,'',autoClip,maxFarPlane,0.0,0.0)

	def getAutoClip(self):
		"""Get whether clip planes will be auto computed based on scene content"""
		return _ipcSend(_VIZ_RENDERNODEGET,self.id,10,'',0.0,0.0,0.0,0.0)

	def getNearFarClip(self):
		"""Get the (near, far) clip planes of the render node projection matrix"""
		return _ipcSend(_VIZ_RENDERNODEGET,self.id,21,'',0.0,0.0,0.0,0.0)

	def setAutoAspectRatio(self, autoAspectRatio):
		"""Set whether projection matrix aspect ratio will be auto computed from viewport"""
		_ipcSend(_VIZ_RENDERNODESET,20,self.id,'',autoAspectRatio,0.0,0.0,0.0)

	def getAutoAspectRatio(self):
		"""Get whether projection matrix aspect ratio will be auto computed from viewport"""
		return _ipcSend(_VIZ_RENDERNODEGET,self.id,20,'',0.0,0.0,0.0,0.0)

	def setCullMask(self, mask, mode=MASK_SET):
		"""Set cull mask fo render node"""
		_ipcSend(_VIZ_RENDERNODESET,11,mask,'',self.id,mode,0.0,0.0)

	def getCullMask(self):
		"""Get the cull mask for the render node"""
		return _ipcSend(_VIZ_RENDERNODEGET,self.id,11,'',0.0,0.0,0.0,0.0)

	def setRenderTexture(self,texture,buffer=AUTO_COMPUTE,face=POSITIVE_X):
		"""Set texture for render node to render onto"""
		if isinstance(texture,VizTexture):
			_ipcSend(_VIZ_RENDERNODESET,3,self.id,'',texture.id,texture._textype,buffer,face)
		elif not texture:
			_ipcSend(_VIZ_RENDERNODESET,3,self.id,'',0,_VIZ_DEL_TEX,buffer,0.0)

	attachTexture = setRenderTexture

	def getRenderTexture(self,buffer=RENDER_COLOR):
		"""Get render texture attached to specified buffer"""
		return _ipcSend(_VIZ_RENDERNODEGET,self.id,3,'',buffer,0.0,0.0,0.0)

	def setRenderTextureOffset(self,offset):
		"""Set the render texture offset"""
		_ipcSend(_VIZ_RENDERNODESET,16,self.id,'',offset[0],offset[1],0.0,0.0)

	def getRenderTextureOffset(self):
		"""Get the render texture offset"""
		return _ipcSend(_VIZ_RENDERNODEGET,self.id,16,'',0.0,0.0,0.0,0.0)

	def setGenerateMipMaps(self, generate):
		"""Set whether to generate mipmaps for render textures"""
		_ipcSend(_VIZ_RENDERNODESET,19,self.id,'',generate,0.0,0.0,0.0)

	def getGenerateMipMaps(self):
		"""Get whether mipmaps are generated for render textures"""
		return _ipcSend(_VIZ_RENDERNODEGET,self.id,19,'',0.0,0.0,0.0,0.0)

	def setMultiSample(self, samples):
		"""Set render texture multisamples"""
		_ipcSend(_VIZ_RENDERNODESET,17,self.id,'',samples,0.0,0.0,0.0)

	def getMultiSample(self):
		"""Get render texture multisamples"""
		return _ipcSend(_VIZ_RENDERNODEGET,self.id,17,'',0.0,0.0,0.0,0.0)

	@DeprecateObject
	def linkViewportSizeToWindow(self,window):
		"""Convenience function that links the viewport size to a window object.
		Returns the created link"""
		self.unlinkViewportSize()
		self._viewportLink = link(window.WindowSize,self,mask=LINK_SCALE,dstFlag=LINK_RENDERNODE_SIZE)
		return self._viewportLink

	@DeprecateObject
	def unlinkViewportSize(self):
		"""Unlinks viewport size from previously linked window"""
		if self._viewportLink:
			self._viewportLink.remove()
			self._viewportLink = None

	def renderOnlyIfNodeVisible(self,nodes):
		"""Render the render node only when at least one of the specified nodes is visible"""
		if nodes:
			_ipcSend(_VIZ_RENDERNODESET,14,self.id,'',1,0.0,0.0,0.0)
			for n in nodes:
				_ipcSend(_VIZ_RENDERNODESET,15,self.id,'',n.id,0.0,0.0,0.0)
		else:
			_ipcSend(_VIZ_RENDERNODESET,14,self.id,'',0,0.0,0.0,0.0)

	def screenToWorld(self, pos, mode=WINDOW_NORMALIZED):
		"""Takes the given 2D coordinates and returns the line that
	passes through it in 3D coordinates, [x1,y1,z1,x2,y2,z2]"""
		return Line(_ipcSend(_VIZ_RENDERNODEGET, self.id, 22,'', pos[0], pos[1], 0.0, mode))

	def worldToScreen(self, pos, mode=WINDOW_NORMALIZED):
		"""Takes the given 3D coordinates and returns the 2D screen coordinates"""
		return _ipcSend(_VIZ_RENDERNODEGET, self.id, 23,'', pos[0], pos[1], pos[2], mode)


class VizUserTracker( VizCustomLinkable):
	"""User tracker object"""
	pass

class VizUser(VizNode):
	"""User object"""

	def setTracker(self, name, linkable, flag=0):
		"""Set a named tracker to the user
		@return VizUserTracker()"""
		linkableType = _getLinkableType(linkable)
		if linkableType < 0:
			raise TypeError('Object is not a linkable')
		return VizUserTracker._GetObject(_ipcSend(_VIZ_CREATELINKABLE,linkable.id,linkableType,name,flag,self.id,0.0,5.0))

	def getTracker(self, name):
		"""Get a named tracker from the user
		@return VizUserTracker()"""
		return VizUserTracker._GetObject(_ipcSend(_VIZ_CREATELINKABLE,self.id,0,name,0.0,0.0,0.0,6.0))

	def setHead(self, linkable, flag=0):
		"""Set the head tracker for the user"""
		return 	self.setTracker(USER_HEAD, linkable, flag)
	def getHead(self):
		"""Get the head tracker for the user"""
		return self.getTracker(USER_HEAD)
	Head = property(getHead, setHead, doc='Head tracker for user')

	def setOrigin(self, linkable, flag=0):
		"""Set the origin tracker for the user"""
		return 	self.setTracker(USER_ORIGIN, linkable, flag)
	def getOrigin(self):
		"""Get the origin tracker for the user"""
		return self.getTracker(USER_ORIGIN)
	Origin = property(getOrigin, setOrigin, doc='Origin tracker for user')

	def setValue(self, name, value):
		"""Set a named value on the user"""
		s = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
		_ipcSend(_VIZ_SETSTRING, 0, 0, name, 0.0, 0.0, 0.0, 0.0)
		_ipcSend(_VIZ_USERSET, 1, self.id, s, 0.0, 0.0, 0.0, 0.0)

	def getValue(self, name, default=None):
		"""Get a named value from the user"""
		s = _ipcSend(_VIZ_USERGET, 1, self.id, name, 0.0, 0.0, 0.0, 0.0)
		try:
			return pickle.loads(s)
		except:
			return default

MainUser = VizUser(0)

class VizAnimationPath(VizLinkable):
	"""VizAnimationPath object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_ANIMATION_PATH
	_VizLinkableType = _VIZ_PATH_LINKABLE

	def __init__(self, id, play=None, loop=None, autoRotate=None, translateMode=None, rotateMode=None, scaleMode=None):
		VizLinkable.__init__(self, id)

		if self.valid():
			if loop is not None:
				self.setLoopMode(loop)
			if autoRotate is not None:
				self.setAutoRotate(autoRotate)
			if translateMode is not None:
				self.setTranslateMode(translateMode)
			if rotateMode is not None:
				self.setRotateMode(rotateMode)
			if scaleMode is not None:
				self.setScaleMode(scaleMode)
			if play:
				self.play()

	def remove(self, points=False):
		"""Delete the animation path.
		points - If True, remove all control points belonging to path as well"""
		_ipcSend(_VIZ_PATHREMOVE,self.id,points,'',0.0,0.0,0.0,0.0)

	def add(self,point,time):
		"""Add a control point to the animation path at the specified control time"""
		if isinstance(point,VizControlPoint):
			_ipcSend(_VIZ_PATHADDPOINT,self.id,point.id,'',time,0.0,0.0,0.0)

	def addControlPoint(self, time, point=None, autoRemove=True, **kw):
		"""Add a control point to the animation path at the specified time"""
		if point is None:
			point = addControlPoint(**kw)
		_ipcSend(_VIZ_PATHADDPOINT,self.id,point.id,'',time,0.0,0.0,0.0)
		if autoRemove:
			self.addRemoveCallback(point.remove)
		return point

	def getControlPointCount(self):
		"""Get number of control points added to path"""
		return _ipcSend(_VIZ_PATHGET,self.id,7,'',0.0,0.0,0.0,0.0)

	def getControlPoint(self, index):
		"""Get control point at specified index"""
		return VizControlPoint._GetObject(_ipcSend(_VIZ_PATHGET,self.id,8,'',index,0.0,0.0,0.0))

	def getControlPointTime(self, index):
		"""Get time of control point at specified index"""
		return _ipcSend(_VIZ_PATHGET,self.id,9,'',index,0.0,0.0,0.0)

	def iterControlPoints(self):
		"""Returns iterator that yields (time, control point) tuples"""
		for x in range(self.getControlPointCount()):
			yield self.getControlPointTime(x), self.getControlPoint(x)

	def removeControlPoint(self, index, remove=True):
		"""Remove the control point at the specified index"""
		_ipcSend(_VIZ_PATHSET,self.id,3,'',index,remove,0.0,0.0)

	def clearControlPoints(self, remove=True):
		"""Clear all control points from the animation path"""
		_ipcSend(_VIZ_PATHSET,self.id,2,'',remove,0.0,0.0,0.0)

	def addEventAtEnd(self, name):
		"""Trigger path event with name when end is reached"""
		_ipcSend(_VIZ_PATHSET,self.id,4,name,1,0.0,0.0,0.0)

	def addEventAtControlPoint(self, name, index):
		"""Trigger path event with name when control point is reached"""
		_ipcSend(_VIZ_PATHSET,self.id,4,name,2,index,0.0,0.0)

	def addEventAtTime(self, name, time):
		"""Trigger path event with name when time is reached"""
		_ipcSend(_VIZ_PATHSET,self.id,4,name,3,time,0.0,0.0)

	def addEventAtDistance(self, name, distance):
		"""Trigger path event with name when distance is reached"""
		_ipcSend(_VIZ_PATHSET,self.id,4,name,4,distance,0.0,0.0)

	def removeEvent(self, name):
		"""Remove all events with the specified name"""
		_ipcSend(_VIZ_PATHSET,self.id,6,name,0.0,0.0,0.0,0.0)

	def clearEvents(self):
		"""Clear all events from the animation path"""
		_ipcSend(_VIZ_PATHSET,self.id,5,'',0.0,0.0,0.0,0.0)

	def setLoopMode(self,mode):
		"""Set the loop mode for the animation path"""
		_ipcSend(_VIZ_PATHLOOPMODE,self.id,mode,'',0.0,0.0,0.0,0.0)
	loop = setLoopMode

	def getLoopMode(self):
		"""Return the loop mode of the animation path"""
		return _ipcSend(_VIZ_PATHGET,self.id,4,'',0.0,0.0,0.0,0.0)

	def setAutoRotate(self,mode=ON):
		"""Turn automatic rotations on/off"""
		_ipcSend(_VIZ_PATHAUTOROT,self.id,mode,'',0.0,0.0,0.0,0.0)

	def getAutoRotate(self):
		"""Return auto rotate mode of animation path"""
		return _ipcSend(_VIZ_PATHGET,self.id,5,'',0.0,0.0,0.0,0.0)

	def setConstantSpeed(self,mode,speed=1):
		"""Set whether to move at a constant speed"""
		_ipcSend(_VIZ_PATHCONSTVEL,self.id,0,'',mode,speed,0.0,0.0)

	def getConstantSpeed(self):
		"""Get constant speed value"""
		return _ipcSend(_VIZ_PATHGET,self.id,10,'',0.0,0.0,0.0,0.0)

	def getConstantSpeedMode(self):
		"""Get constant speed mode"""
		return _ipcSend(_VIZ_PATHGET,self.id,11,'',0.0,0.0,0.0,0.0)

	def setTranslateMode(self,mode):
		"""Set the interpolation mode for translations"""
		if mode == LINEAR:
			mode = LINEAR_INTERP
		_ipcSend(_VIZ_PATHINTERPMODE,self.id,0,'',mode,0.0,0.0,0.0)

	def getTranslateMode(self):
		"""Get the interpolation mode for translations"""
		return _ipcSend(_VIZ_PATHGET,self.id,6,'',0.0,0.0,0.0,0.0)

	def setRotateMode(self,mode):
		"""Set the interpolation mode for rotations"""
		if mode == LINEAR:
			mode = LINEAR_INTERP
		_ipcSend(_VIZ_PATHINTERPMODE,self.id,1,'',mode,0.0,0.0,0.0)

	def getRotateMode(self):
		"""Get the interpolation mode for rotations"""
		return _ipcSend(_VIZ_PATHGET,self.id,6,'',1.0,0.0,0.0,0.0)

	def setScaleMode(self,mode):
		"""Set the interpolation mode for scale"""
		if mode == LINEAR:
			mode = LINEAR_INTERP
		_ipcSend(_VIZ_PATHINTERPMODE,self.id,2,'',mode,0.0,0.0,0.0)

	def getScaleMode(self):
		"""Get the interpolation mode for scale"""
		return _ipcSend(_VIZ_PATHGET,self.id,6,'',2.0,0.0,0.0,0.0)

	def setSpeed(self,value):
		"""Set the speed of the animation path"""
		_ipcSend(_VIZ_PATHSPEED,self.id,0,'',value,0.0,0.0,0.0)
	speed = setSpeed

	def getSpeed(self):
		"""Return speed of animation path"""
		return _ipcSend(_VIZ_PATHGET,self.id,3,'',0.0,0.0,0.0,0.0)

	def setPaused(self, mode):
		"""Set paused mode of animation path"""
		_ipcSend(_VIZ_PATHPAUSE,self.id,mode,'',0.0,0.0,0.0,0.0)

	def getPaused(self):
		"""Return whether the animation path is paused"""
		return _ipcSend(_VIZ_PATHGET,self.id,12,'',0.0,0.0,0.0,0.0)

	def pause(self):
		"""Pause the animation path"""
		self.setPaused(True)

	def play(self):
		"""Play the animation path"""
		self.setPaused(False)

	def reset(self):
		"""Reset the animation path"""
		_ipcSend(_VIZ_PATHRESET,self.id,0,'',0.0,0.0,0.0,0.0)

	def computeTangents(self):
		"""Automatically compute tangents for translations"""
		_ipcSend(_VIZ_PATHCOMPUTETAN,self.id,0,'',0.0,0.0,0.0,0.0)

	def getDuration(self):
		"""Return duration of animation path in seconds"""
		return _ipcSend(_VIZ_PATHGET,self.id,1,'',0.0,0.0,0.0,0.0)

	def setTime(self, time):
		"""Set time of animation path in seconds"""
		_ipcSend(_VIZ_PATHSET,self.id,1,'',time,0.0,0.0,0.0)

	def getTime(self):
		"""Return current time of animation path in seconds"""
		return _ipcSend(_VIZ_PATHGET,self.id,2,'',0.0,0.0,0.0,0.0)

	def getMatrixAtTime(self, time):
		"""Return the matrix of the animation path at the specified time"""
		return Transform(_ipcSend(_VIZ_PATHGET,self.id,13,'',time,0.0,0.0,0.0))

	def getDistance(self):
		"""Return the total distance traveled through one loop of the animation path"""
		return _ipcSend(_VIZ_PATHGET,self.id,14,'',0.0,0.0,0.0,0.0)

	def getDistanceAtTime(self, time):
		"""Return the total distance traveled at the specified time of the animation path"""
		return _ipcSend(_VIZ_PATHGET,self.id,15,'',time,0.0,0.0,0.0)

	def getDistanceAtControlPoint(self, index):
		"""Return the total distance traveled at the specified control point in the animation path"""
		return _ipcSend(_VIZ_PATHGET,self.id,17,'',index,0.0,0.0,0.0)

	def getTimeAtDistance(self, distance):
		"""Return the elapsed time at the specified distance along the animation path"""
		return _ipcSend(_VIZ_PATHGET,self.id,16,'',distance,0.0,0.0,0.0)

	def getTimeAtControlPoint(self, index):
		"""Return the elapsed time at the specified control point in the animation path"""
		return _ipcSend(_VIZ_PATHGET,self.id,18,'',index,0.0,0.0,0.0)

class VizControlPoint(VizLinkable):
	"""VizControlPoint object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_CONTROL_POINT
	_VizLinkableType = _VIZ_CONTROL_POINT_LINKABLE

	def __init__(self, id, pos=None, quat=None, euler=None, axisAngle=None, scale=None):
		VizLinkable.__init__(self, id)

		if self.valid():
			if pos is not None:
				self.setPosition(pos)
			if quat is not None:
				self.setQuat(quat)
			if euler is not None:
				self.setEuler(euler)
			if axisAngle is not None:
				self.setAxisAngle(axisAngle)
			if scale is not None:
				self.setScale(scale)

	def remove(self):
		"""Delete the control point"""
		_ipcSend(_VIZ_CPREMOVE,self.id,0,'',0.0,0.0,0.0,0.0)

	def setPosition(self,x,y=0,z=0):
		"""Set the translate value of the control point"""
		if _islist(x):
			_ipcSend(_VIZ_POINTDATA,self.id,0,'',x[0],x[1],x[2],0.0)
		else:
			_ipcSend(_VIZ_POINTDATA,self.id,0,'',x,y,z,0.0)

	def setQuat(self,x,y=0,z=0,w=0):
		"""Set the rotate value of the control point"""
		if _islist(x):
			_ipcSend(_VIZ_POINTDATA,self.id,1,'',x[0],x[1],x[2],x[3])
		else:
			_ipcSend(_VIZ_POINTDATA,self.id,1,'',x,y,z,w)

	def setEuler(self,x,y=0,z=0):
		"""Set the rotate value of the control point"""
		if _islist(x):
			q = vizmat.EulerToQuat(x)
		else:
			q = vizmat.EulerToQuat(x,y,z)
		_ipcSend(_VIZ_POINTDATA,self.id,1,'',q[0],q[1],q[2],q[3])

	def setAxisAngle(self,x,y=0,z=0,deg=0):
		"""Set the rotate value of the control point"""
		if _islist(x):
			q = vizmat.AxisAngleToQuat(x)
		else:
			q = vizmat.AxisAngleToQuat(x,y,z,deg)
		_ipcSend(_VIZ_POINTDATA,self.id,1,'',q[0],q[1],q[2],q[3])

	def setScale(self,x,y=0,z=0):
		"""Set the scale value of the control point"""
		if _islist(x):
			_ipcSend(_VIZ_POINTDATA,self.id,2,'',x[0],x[1],x[2],0.0)
		else:
			_ipcSend(_VIZ_POINTDATA,self.id,2,'',x,y,z,0.0)

	def setTranslateMode(self,mode):
		"""Set the interpolation mode for translations"""
		if mode == LINEAR:
			mode = LINEAR_INTERP
		_ipcSend(_VIZ_POINTINTERP,self.id,0,'',mode,0.0,0.0,0.0)

	def setRotateMode(self,mode):
		"""Set the interpolation mode for rotations"""
		if mode == LINEAR:
			mode = LINEAR_INTERP
		_ipcSend(_VIZ_POINTINTERP,self.id,1,'',mode,0.0,0.0,0.0)

	def setScaleMode(self,mode):
		"""Set the interpolation mode for scale"""
		if mode == LINEAR:
			mode = LINEAR_INTERP
		_ipcSend(_VIZ_POINTINTERP,self.id,2,'',mode,0.0,0.0,0.0)

	def setPositionIn(self,x,y=0,z=0):
		if _islist(x):
			_ipcSend(_VIZ_POINTDATAIN,self.id,0,'',x[0],x[1],x[2],0.0)
		else:
			_ipcSend(_VIZ_POINTDATAIN,self.id,0,'',x,y,z,0.0)

	def setPositionOut(self,x,y=0,z=0):
		if _islist(x):
			_ipcSend(_VIZ_POINTDATAOUT,self.id,0,'',x[0],x[1],x[2],0.0)
		else:
			_ipcSend(_VIZ_POINTDATAOUT,self.id,0,'',x,y,z,0.0)

class VizShader(VizObject):
	"""VizShader object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_SHADER

	def __init__(self, id, vert=None, frag=None, geom=None, uniforms=None):
		VizObject.__init__(self, id)

		if self.valid():
			if vert is not None:
				self.loadVertex(vert)
			if frag is not None:
				self.loadFragment(frag)
			if geom is not None:
				self.loadGeometry(geom)
			if uniforms is not None:
				self.attach(uniforms)

	def remove(self):
		"""Permanently remove the shader"""
		_ipcSend(_VIZ_SHADERSET,self.id,4,'',0.0,0.0,0.0,0.0)

	def unapply(self):
		"""Unapply shader from all objects"""
		_ipcSend(_VIZ_SHADERSET,self.id,10,'',0.0,0.0,0.0,0.0)

	def loadGeometry(self,shader):
		"""Load a geometry shader"""
		if '\n' in shader:
			self.loadGeometryCode(shader)
		else:
			self.loadGeometryFile(shader)

	def loadVertex(self,shader):
		"""Load a vertex shader"""
		if '\n' in shader:
			self.loadVertexCode(shader)
		else:
			self.loadVertexFile(shader)

	def loadFragment(self,shader):
		"""Load a fragment shader"""
		if '\n' in shader:
			self.loadFragmentCode(shader)
		else:
			self.loadFragmentFile(shader)

	def loadGeometryFile(self,file):
		"""Load a geometry shader from a file"""
		return _ipcSend(_VIZ_SHADERSET,self.id,8,file,0.0,0.0,0.0,0.0)

	def loadVertexFile(self,file):
		"""Load a vertex shader from a file"""
		return _ipcSend(_VIZ_SHADERSET,self.id,0,file,0.0,0.0,0.0,0.0)

	def loadFragmentFile(self,file):
		"""Load a fragment shader from a file"""
		return _ipcSend(_VIZ_SHADERSET,self.id,2,file,0.0,0.0,0.0,0.0)

	def loadGeometryCode(self,code):
		"""Load a geometry shader from code"""
		return _ipcSend(_VIZ_SHADERSET,self.id,9,code,0.0,0.0,0.0,0.0)

	def loadVertexCode(self,code):
		"""Load a vertex shader from code"""
		return _ipcSend(_VIZ_SHADERSET,self.id,1,code,0.0,0.0,0.0,0.0)

	def loadFragmentCode(self,code):
		"""Load a fragment shader from code"""
		return _ipcSend(_VIZ_SHADERSET,self.id,3,code,0.0,0.0,0.0,0.0)

	def attach(self,*args):
		"""Attach a uniform to a shader"""
		for u in args:
			if _islist(u):
				self.attach(*u)
			else:
				_ipcSend(_VIZ_SHADERSET,self.id,5,'',u.id,0.0,0.0,0.0)

	def detach(self,*args):
		"""Detach a uniform from a shader"""
		for u in args:
			if _islist(u):
				self.detach(*u)
			else:
				_ipcSend(_VIZ_SHADERSET,self.id,6,'',u.id,0.0,0.0,0.0)

	def setAttribute(self,name,index):
		"""Set the index for a vertex attribute"""
		if index is None:
			index = -1
		_ipcSend(_VIZ_SHADERSET,self.id,7,name,index,0.0,0.0,0.0)

class VizUniform(VizLinkable):
	"""VizUniform object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_UNIFORM
	_VizLinkableType = _VIZ_UNIFORM_LINKABLE

	def __init__(self, id):
		VizLinkable.__init__(self, id)

	def __len__(self):
		return _ipcSend(_VIZ_UNIFORMGET,self.id,3,'',0.0,0.0,0.0,0.0)

	def __getitem__(self, k):
		if isinstance(k,slice):
			indices = range(len(self)).__getitem__(k)
			return [ self.get(i) for i in indices ]
		elif k < 0:
			return self.get(len(self)+k)
		else:
			return self.get(k)

	def __setitem__(self, k, value):
		if isinstance(k,slice):
			start,stop,step = k.indices(len(self))
			if len(value) != (stop - start):
				raise ValueError('Value length is not equal to slice length')
			for index,val in zip(range(start,stop),value):
				self.set(val,index)
		elif k < 0:
			self.set(value,len(self)+k)
		else:
			self.set(value,k)

	def __iter__(self):
		for x in range(len(self)):
			yield self.get(x)

	def remove(self):
		"""Permanently remove the uniform"""
		_ipcSend(_VIZ_UNIFORMREMOVE,self.id,0,'',0.0,0.0,0.0,0.0)

	def unapply(self):
		"""Unapply uniform from all objects"""
		_ipcSend(_VIZ_UNIFORMREMOVE,self.id,1,'',0.0,0.0,0.0,0.0)

	def getName(self):
		"""Get the name of the uniform"""
		return _ipcSend(_VIZ_UNIFORMGET,self.id,1,'',0.0,0.0,0.0,0.0)

	def getDataType(self):
		"""Get the data type of the uniform"""
		return _ipcSend(_VIZ_UNIFORMGET,self.id,4,'',0.0,0.0,0.0,0.0)

	def get(self,index=0):
		"""Get the value of the uniform"""
		return _ipcSend(_VIZ_UNIFORMGET,self.id,2,'',index,0.0,0.0,0.0)

	def setName(self,name):
		"""Set new name for uniform"""
		_ipcSend(_VIZ_UNIFORMREMOVE,self.id,2,name,0.0,0.0,0.0,0.0)

	def set(self,value,index=0):
		"""Set the value of the uniform"""

		if _islist(value):
			data = list(value)
		else:
			data = [value]

		data += [0,0,0]

		_ipcSend(_VIZ_SETUNIFORM,self.id,index,'',*data[:4])

class VizUniformMat3(VizUniform):
	def set(self,value,index=0):
		"""Set the value of the uniform"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', value[0], value[1], value[2], 0.0)
		_ipcSend(_VIZ_SETMATRIX2, 0, 0, '', value[3], value[4], value[5], 0.0)
		_ipcSend(_VIZ_SETUNIFORM,self.id,index,'',value[6],value[7],value[8],0.0)

class VizUniformMat4(VizUniform):
	def set(self,value,index=0):
		"""Set the value of the uniform"""
		_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', *value[0:4])
		_ipcSend(_VIZ_SETMATRIX2, 0, 0, '', *value[4:8])
		_ipcSend(_VIZ_SETMATRIX3, 0, 0, '', *value[8:12])
		_ipcSend(_VIZ_SETUNIFORM,self.id,index,'',*value[12:16])

class VizEffect(VizObject):
	"""VizEffect object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_EFFECT

	def __init__(self, id, removeFlags=None):
		VizObject.__init__(self, id)

		if self.valid():
			if removeFlags is not None:
				self.setRemoveFlags(removeFlags)

	def remove(self):
		"""Permanently remove the effect"""
		_ipcSend(_VIZ_EFFECTSET, 1, self.id, '',0.0,0.0,0.0,0.0)

	def unapply(self, flags=UNAPPLY_ALL):
		"""Unapply effect from all objects"""
		_ipcSend(_VIZ_EFFECTSET, 3, self.id, '',flags,0.0,0.0,0.0)

	def setRemoveFlags(self, flags):
		"""Set unapply flags to execute when effect is removed"""
		self.setProperty('effect.remove_flags',flags)

	def getRemoveFlags(self):
		"""Get unapply flags to execute when effect is removed"""
		return int(self.getProperty('effect.remove_flags'))

	def setEnabled(self, mode):
		"""Set whether the effect is enabled"""
		_ipcSend(_VIZ_EFFECTSET, 10, self.id, '',mode,0.0,0.0,0.0)

	def getEnabled(self):
		"""Set whether the effect is enabled"""
		return _ipcSend(_VIZ_EFFECTGET, 2, self.id, '',0.0,0.0,0.0,0.0)

	def setProperty(self, name, value, index=0):
		"""Set the value of an effect property"""
		if isinstance(value,VizTexture):
			_ipcSend(_VIZ_EFFECTSET, 12, self.id, name,value.id,value._textype,0.0,0.0)
		else:
			if _islist(value) or isinstance(value,Matrix):
				data = list(value)
			else:
				data = [value]

			size = len(data)
			if size > 4:
				if size < 16:
					data += [0] * (16-size) # Ensure at least 16 values
				_ipcSend(_VIZ_SETMATRIX1, 0, 0, '', *data[0:4])
				_ipcSend(_VIZ_SETMATRIX2, 0, 0, '', *data[4:8])
				_ipcSend(_VIZ_SETMATRIX3, 0, 0, '', *data[8:12])
				_ipcSend(_VIZ_EFFECTSETMAT, self.id, index, name, data[12], data[13], data[14], data[15])
			else:
				data += [0,0,0]
				_ipcSend(_VIZ_EFFECTSETPROP, self.id, index, name, data[0], data[1], data[2], data[3])

	def getProperty(self, name, index=0):
		"""Get the value of an effect property"""
		return _ipcSend(_VIZ_EFFECTGET, 1, self.id, name,index,0.0,0.0,0.0)

	def getPropertySize(self, name):
		"""Get the array size of an effect property"""
		return _ipcSend(_VIZ_EFFECTGET, 7, self.id, name,0.0,0.0,0.0,0.0)

	def getName(self):
		"""Get the name of the effect"""
		return _ipcSend(_VIZ_EFFECTGET, 3, self.id, '',0.0,0.0,0.0,0.0)

	def getTypeName(self):
		"""Get the type name of the effect"""
		return _ipcSend(_VIZ_EFFECTGET, 4, self.id, '',0.0,0.0,0.0,0.0)

class VizEffectComposer(VizObject):
	"""VizEffectComposer object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_COMPOSER

	def __init__(self, id):
		VizObject.__init__(self, id)

	def remove(self):
		"""Permanently remove the effect composer"""
		_ipcSend(_VIZ_EFFECTSET, 2, self.id, '',0.0,0.0,0.0,0.0)

	def unapply(self):
		"""Unapply effect composer from all objects"""
		_ipcSend(_VIZ_EFFECTSET, 4, self.id, '',0.0,0.0,0.0,0.0)

	def addGlobals(self, source):
		"""Add global variables to the composer"""
		_ipcSend(_VIZ_EFFECTSET, 13, self.id, source,0.0,0.0,0.0,0.0)

	def addEffect(self, effect):
		"""Add an effect to the composer"""
		if _islist(effect):
			for e in effect:
				_ipcSend(_VIZ_EFFECTSET, 7, self.id, '',e.id,0.0,0.0,0.0)
		else:
			_ipcSend(_VIZ_EFFECTSET, 7, self.id, '',effect.id,0.0,0.0,0.0)

	def removeEffect(self, effect):
		"""Remove an effect from the composer"""
		if _islist(effect):
			for e in effect:
				_ipcSend(_VIZ_EFFECTSET, 8, self.id, '',e.id,0.0,0.0,0.0)
		else:
			_ipcSend(_VIZ_EFFECTSET, 8, self.id, '',effect.id,0.0,0.0,0.0)

	def clearEffects(self):
		"""Clear all effects from the composer"""
		_ipcSend(_VIZ_EFFECTSET, 11, self.id, '',0.0,0.0,0.0,0.0)

	def getEffectList(self):
		"""Get list of effects added to composer"""
		vals = _ipcSend(_VIZ_EFFECTGET, 6, self.id, '',0.0,0.0,0.0,0.0)
		return [ VizEffect._GetObject(id) for id in vals ]

	def getName(self):
		"""Get the name of the composer"""
		return _ipcSend(_VIZ_EFFECTGET, 5, self.id, '',0.0,0.0,0.0,0.0)

class VizOperator(object):
	"""VizOperator object"""
	def __init__(self, id, parent):
		self.id = int(id)
		self.parent = parent

	def __eq__(self, other):
		if isinstance(other, VizOperator):
			return self.id == other.id and self.parent == other.parent
		return NotImplemented

	def __hash__(self):
		return hash((self.id, self.parent))

	def __bool__(self):
		return self.id > -1

	def __int__(self):
		return self.id

	def valid(self):
		return self.id > -1

	def remove(self):
		"""Remove the operator from the link object"""
		_ipcSend(_VIZ_LINKSET,self.parent,_LINK_REMOVE_OP,'',self.id,0.0,0.0,0.0)
		self.id = -1

	def set(self,x,y=0,z=0,w=0):
		"""Set the value of the operator"""
		if _islist(x):
			if len(x) == 3:
				_ipcSend(_VIZ_LINKSETOP,self.parent,self.id,'',x[0],x[1],x[2],0.0)
			else:
				_ipcSend(_VIZ_LINKSETOP,self.parent,self.id,'',x[0],x[1],x[2],x[3])
		else:
			_ipcSend(_VIZ_LINKSETOP,self.parent,self.id,'',x,y,z,w)

	def get(self):
		"""Get the value of the operator"""
		return _ipcSend(_VIZ_LINKGET,self.parent,_LINK_OPERATOR,'',self.id,0.0,0.0,0.0)

class VizPosOperator(VizOperator):
	setPosition = VizOperator.set
	def getPosition(self):
		"""Get the position representation of the operator"""
		return self.get()[:3]

class VizOriOperator(VizOperator):
	setQuat = VizOperator.set

	def setEuler(self,*args):
		"""Set the euler value of the operator"""
		self.set(vizmat.EulerToQuat(*args))

	def setAxisAngle(self,*args):
		"""Set the axis-angle value of the operator"""
		self.set(vizmat.AxisAngleToQuat(*args))

	getQuat = VizOperator.get

	def getEuler(self):
		"""Get the euler representation of the operator"""
		return vizmat.QuatToEuler(self.get())

	def getAxisAngle(self):
		"""Get the axis-angle representation of the operator"""
		return vizmat.QuatToAxisAngle(self.get())

class VizScaleOperator(VizOperator):
	setScale = VizOperator.set
	def getScale(self):
		"""Get the scale representation of the operator"""
		return self.get()[:3]

class VizScaleOffsetOperator(VizOperator):
	setOffset = VizOperator.set
	def getOffset(self):
		"""Get the scale offset of the operator"""
		return self.get()[:3]

class VizSetPosOperator(VizOperator):
	def setPosition(self,x,y=0,z=0):
		"""Set the position of the operator"""
		mask = 0
		if _islist(x):
			x,y,z = x
		if x is None:
			x = 0.0
		else:
			mask = mask | RESET_X
		if y is None:
			y = 0.0
		else:
			mask = mask | RESET_Y
		if z is None:
			z = 0.0
		else:
			mask = mask | RESET_Z
		self.set(x,y,z,mask)

	def getPosition(self):
		"""Get the position representation of the operator"""
		val = self.get()
		mask = int(val[3])
		if not mask & RESET_X:
			val[0] = None
		if not mask & RESET_Y:
			val[1] = None
		if not mask & RESET_Z:
			val[2] = None
		return val[:3]

class VizSetEulerOperator(VizOperator):
	def setEuler(self,x,y=0,z=0):
		"""Set the euler of the operator"""
		mask = 0
		if _islist(x):
			x,y,z = x
		if x is None:
			x = 0.0
		else:
			mask = mask | RESET_X
		if y is None:
			y = 0.0
		else:
			mask = mask | RESET_Y
		if z is None:
			z = 0.0
		else:
			mask = mask | RESET_Z
		self.set(x,y,z,mask)

	def getEuler(self):
		"""Get the euler representation of the operator"""
		val = self.get()
		mask = int(val[3])
		if not mask & RESET_X:
			val[0] = None
		if not mask & RESET_Y:
			val[1] = None
		if not mask & RESET_Z:
			val[2] = None
		return val[:3]

class VizSwapPosOperator(VizOperator):
	setSwap = VizOperator.set
	def getSwap(self):
		"""Get the swap values"""
		return [ int(x) for x in self.get()[:3] ]

class VizSwapQuatOperator(VizOperator):
	setSwap = VizOperator.set
	def getSwap(self):
		"""Get the swap values"""
		return [ int(x) for x in self.get() ]

class VizSwapEulerOperator(VizOperator):
	setSwap = VizOperator.set
	def getSwap(self):
		"""Get the swap values"""
		return [ int(x) for x in self.get()[:3] ]

class VizClampPosOperator(VizOperator):
	def setRange(self,minVal,maxVal=0):
		"""Set the clamp range"""
		mask = 0
		if _islist(minVal):
			minVal,maxVal = minVal
		if minVal is None:
			minVal = 0.0
		else:
			mask = mask | 1
		if maxVal is None:
			maxVal = 0.0
		else:
			mask = mask | 2
		self.set(minVal,maxVal,self.axis,mask)
	def getRange(self):
		"""Get the clamp range"""
		val = self.get()
		mask = int(val[3])
		if not mask & 1:
			val[0] = None
		if not mask & 2:
			val[1] = None
		return val[:2]

class VizSnapPosOperator(VizOperator):

	def setIncrement(self, value):
		"""Set the snap increment"""
		self.set(0,value,0,0)

	def getIncrement(self):
		"""Set the snap increment"""
		return self.get()[0]

	def setThreshold(self, value):
		"""Set the snap threshold"""
		if value is None:
			value = -1.0
		self.set(1,value,0,0)

	def getThreshold(self):
		"""Get the snap threshold"""
		value = self.get()[1]
		if value < 0.0:
			value = None
		return value

	def setAxis(self, value):
		"""Set the snap axis mask"""
		self.set(2,value,0,0)

	def getAxis(self):
		"""Get the snap axis mask"""
		return int(self.get()[2])

class VizLinkableOperator(VizOperator):
	def setLinkable(self,linkable,mask=LINK_POS|LINK_ORI,flag=0):
		"""Set the linkable of the operator"""
		linkableType = _getLinkableType(linkable)
		if linkableType < 0:
			raise TypeError('Object is not a linkable')
		self.set(linkable.id,linkableType,mask,flag)
	def getLinkable(self):
		"""Get the linkable of the operator"""
		data = self.get()
		return _getLinkableObj(int(data[0]),int(data[1]))

class VizLookAtOperator(VizOperator):
	def setLinkable(self,linkable,flag=0):
		"""Set the linkable of the operator"""
		linkableType = _getLinkableType(linkable)
		if linkableType < 0:
			raise TypeError('Object is not a linkable')
		self.set(linkable.id,linkableType,flag)
	def getLinkable(self):
		"""Get the linkable of the operator"""
		data = self.get()
		return _getLinkableObj(int(data[0]),int(data[1]))


class VizInvertOperator(VizOperator):
	pass

class VizLink(VizLinkable):
	"""VizLink object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_LINK
	_VizLinkableType = _VIZ_LINK_LINKABLE

	def __init__(self, id, mask=None, srcFlag=None, dstFlag=None, offset=None, enabled=None, srcMaskOverride=None):
		VizLinkable.__init__(self, id)

		if self.valid():
			if mask is not None:
				self.setMask(mask)
			if srcMaskOverride is not None:
				self.setSrcMaskOverride(srcMaskOverride)
			if srcFlag is not None:
				self.setSrcFlag(srcFlag)
			if dstFlag is not None:
				self.setDstFlag(dstFlag)
			if offset is not None:
				self.setOffset(offset)
			if enabled is not None:
				self.setEnabled(enabled)

	def remove(self):
		"""Remove the link between the two objects"""
		_ipcSend(_VIZ_LINKSET,self.id,_LINK_REMOVE,'',0.0,0.0,0.0,0.0)

	def setSrc(self,src):
		"""Set the source linkable object of the link"""
		srcType = _getLinkableType(src)

		if srcType < 0:
			raise TypeError('Source object is not a linkable type')

		_ipcSend(_VIZ_LINKSET,self.id,_LINK_SRC,'',src.id,srcType,0.0,0.0)

	def setDst(self,dst):
		"""Set the destination linkable object of the link"""
		dstType = _getLinkableType(dst)

		if dstType < 0:
			raise TypeError('Destination object is not a linkable type')

		_ipcSend(_VIZ_LINKSET,self.id,_LINK_DST,'',dst.id,dstType,0.0,0.0)

	def getSrc(self):
		"""Get the source linkable object of the link"""
		id,type = _ipcSend(_VIZ_LINKGET,self.id,_LINK_SRC,'',0.0,0.0,0.0,0.0)
		return _getLinkableObj(id,type)

	def getDst(self):
		"""Get the destination linkable object of the link"""
		id,type = _ipcSend(_VIZ_LINKGET,self.id,_LINK_DST,'',0.0,0.0,0.0,0.0)
		return _getLinkableObj(id,type)

	def setMask(self,mask):
		"""Set the link mask"""
		_ipcSend(_VIZ_LINKSET,self.id,_LINK_MASK,'',mask,0.0,0.0,0.0)

	def getMask(self):
		"""Get the link mask"""
		return _ipcSend(_VIZ_LINKGET,self.id,_LINK_MASK,'',0.0,0.0,0.0,0.0)

	def getSrcMask(self):
		"""Get the mask of the source object"""
		return _ipcSend(_VIZ_LINKGET,self.id,_LINK_SRC_MASK,'',0.0,0.0,0.0,0.0)

	def getDstMask(self):
		"""Get the mask of the destination object"""
		return _ipcSend(_VIZ_LINKGET,self.id,_LINK_DST_MASK,'',0.0,0.0,0.0,0.0)

	def setSrcMaskOverride(self,mask):
		"""Set the source mask override value.
		This mask will be combined with the existing source mask,
		forcing the link to provide data that is not otherwise provided by the source object"""
		_ipcSend(_VIZ_LINKSET,self.id,14,'',mask,0.0,0.0,0.0)

	def getSrcMaskOverride(self):
		"""Get the source mask override value"""
		return _ipcSend(_VIZ_LINKGET,self.id,14,'',0.0,0.0,0.0,0.0)

	def setSrcFlag(self,flag):
		"""Set the the flag for retrieving values from the source object"""
		_ipcSend(_VIZ_LINKSET,self.id,_LINK_SRC_FLAG,'',flag,0.0,0.0,0.0)

	def getSrcFlag(self):
		"""Get the flag for retrieving values from the source object"""
		return _ipcSend(_VIZ_LINKGET,self.id,_LINK_SRC_FLAG,'',0.0,0.0,0.0,0.0)

	def setDstFlag(self,flag):
		"""Set the flag for setting values for the destination object"""
		_ipcSend(_VIZ_LINKSET,self.id,_LINK_DST_FLAG,'',flag,0.0,0.0,0.0)

	def getDstFlag(self):
		"""Get the flag for setting values for the destination object"""
		return _ipcSend(_VIZ_LINKGET,self.id,_LINK_DST_FLAG,'',0.0,0.0,0.0,0.0)

	def setEnabled(self,flag):
		"""Set whether the link is enabled"""
		_ipcSend(_VIZ_LINKSET,self.id,_LINK_ENABLED,'',flag,0.0,0.0,0.0)
	def enable(self): self.setEnabled(True)
	def disable(self): self.setEnabled(False)

	def getEnabled(self):
		"""Get whether the link is enabled"""
		return _ipcSend(_VIZ_LINKGET,self.id,_LINK_ENABLED,'',0.0,0.0,0.0,0.0)

	def update(self):
		"""Manually update the link"""
		_ipcSend(_VIZ_LINKSET,self.id,_LINK_UPDATE,'',0.0,0.0,0.0,0.0)

	def reset(self,flag):
		"""Reset the link using the specified reset flag"""
		_ipcSend(_VIZ_LINKSET,self.id,_LINK_RESET,'',flag,0.0,0.0,0.0)

	def setOffset(self,val):
		"""Set the positional offset for the link"""
		_ipcSend(_VIZ_LINKSET,self.id,_LINK_OFFSET,'',val[0],val[1],val[2],0.0)

	def getOffset(self):
		"""Get the positional offset of the link"""
		return _ipcSend(_VIZ_LINKGET,self.id,_LINK_OFFSET,'',0.0,0.0,0.0,0.0)

	def preQuat(self,val,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will pre-multiply with a quaternion matrix"""
		if not _islist(val):
			raise TypeError('preQuat() parameter must be a list')
		op = VizOriOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_PRE_ROT,priority,target,0.0),self.id)
		op.set(val)
		return op

	def postQuat(self,val,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will post-multiply with a quaternion matrix"""
		if not _islist(val):
			raise TypeError('postQuat() parameter must be a list')
		op = VizOriOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_POST_ROT,priority,target,0.0),self.id)
		op.set(val)
		return op

	def preEuler(self,val,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will pre-multiply with an euler matrix"""
		if not _islist(val):
			raise TypeError('preEuler() parameter must be a list')
		return self.preQuat(vizmat.EulerToQuat(val),priority,target)

	def postEuler(self,val,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will post-multiply with an euler matrix"""
		if not _islist(val):
			raise TypeError('postEuler() parameter must be a list')
		return self.postQuat(vizmat.EulerToQuat(val),priority,target)

	def preAxisAngle(self,val,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will pre-multiply with an axis-angle matrix"""
		if not _islist(val):
			raise TypeError('preAxisAngle() parameter must be a list')
		return self.preQuat(vizmat.AxisAngleToQuat(val),priority,target)

	def postAxisAngle(self,val,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will post-multiply with an axis-angle matrix"""
		if not _islist(val):
			raise TypeError('postAxisAngle() parameter must be a list')
		return self.postQuat(vizmat.AxisAngleToQuat(val),priority,target)

	def preTrans(self,val,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will pre-multiply with a translation matrix"""
		if not _islist(val):
			raise TypeError('preTrans() parameter must be a list')
		op = VizPosOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_PRE_TRANS,priority,target,0.0),self.id)
		op.set(val)
		return op

	def postTrans(self,val,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will post-multiply with a translation matrix"""
		if not _islist(val):
			raise TypeError('postTrans() parameter must be a list')
		op = VizPosOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_POST_TRANS,priority,target,0.0),self.id)
		op.set(val)
		return op

	def preScale(self,val,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will pre-multiply with a scale matrix"""
		if not _islist(val):
			raise TypeError('preScale() parameter must be a list')
		op = VizScaleOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_PRE_SCALE,priority,target,0.0),self.id)
		op.set(val)
		return op

	def postScale(self,val,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will post-multiply with a scale matrix"""
		if not _islist(val):
			raise TypeError('postScale() parameter must be a list')
		op = VizScaleOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_POST_SCALE,priority,target,0.0),self.id)
		op.set(val)
		return op

	def offsetScale(self,offset,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will apply an offset to the scale value"""
		op = VizScaleOffsetOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_SCALE_OFFSET,priority,target,0.0),self.id)
		op.setOffset(offset)
		return op

	def setPos(self,val,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will set the translation to a specified value"""
		op = VizSetPosOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_SET_POS,priority,target,0.0),self.id)
		op.setPosition(val)
		return op

	def setEuler(self,val,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will set the euler rotation to a specified value"""
		op = VizSetEulerOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_SET_EULER,priority,target,0.0),self.id)
		op.setEuler(val)
		return op

	def scaleEuler(self, scale, priority=0, target=LINK_FULL_OP):
		"""Add an operator that will scale the euler rotation by the specified values"""
		op = VizScaleOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_SCALE_EULER,priority,target,0.0),self.id)
		op.setScale(scale)
		return op

	def swapPos(self,val,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will swap the position values"""
		op = VizSwapPosOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_SWAP_POS,priority,target,0.0),self.id)
		op.setSwap(val)
		return op

	def swapQuat(self,val,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will swap the quaternion values"""
		op = VizSwapQuatOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_SWAP_QUAT,priority,target,0.0),self.id)
		op.setSwap(val)
		return op

	def swapEuler(self,val,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will swap the euler values"""
		op = VizSwapEulerOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_SWAP_EULER,priority,target,0.0),self.id)
		op.setSwap(val)
		return op

	def clampPosX(self,val,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will clamp the x position between a specified range"""
		op = VizClampPosOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_CLAMP_POS,priority,target,0.0),self.id)
		op.axis = 0
		op.setRange(val)
		return op

	def clampPosY(self,val,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will clamp the y position between a specified range"""
		op = VizClampPosOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_CLAMP_POS,priority,target,0.0),self.id)
		op.axis = 1
		op.setRange(val)
		return op

	def clampPosZ(self,val,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will clamp the z position between a specified range"""
		op = VizClampPosOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_CLAMP_POS,priority,target,0.0),self.id)
		op.axis = 2
		op.setRange(val)
		return op

	def snapPos(self, increment, threshold=None, axis=LINK_AXIS_ALL, priority=0, target=LINK_FULL_OP):
		"""Add an operator that will snap the position values to the nearest increment"""
		op = VizSnapPosOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_SNAP_POS,priority,target,0.0),self.id)
		op.setIncrement(increment)
		op.setThreshold(threshold)
		op.setAxis(axis)
		return op

	def preMultLinkable(self,linkable,mask=LINK_POS|LINK_ORI,flag=0,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will pre-multiply with the matrix value of a linkable"""
		op = VizLinkableOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_PRE_LINKABLE,priority,target,0.0),self.id)
		op.setLinkable(linkable,mask,flag)
		return op

	def postMultLinkable(self,linkable,mask=LINK_POS|LINK_ORI,flag=0,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will post-multiply with the matrix value of a linkable"""
		op = VizLinkableOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_POST_LINKABLE,priority,target,0.0),self.id)
		op.setLinkable(linkable,mask,flag)
		return op

	def preMultInverseLinkable(self,linkable,mask=LINK_POS|LINK_ORI,flag=0,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will pre-multiply with the inverse matrix value of a linkable"""
		op = VizLinkableOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_PRE_INV_LINKABLE,priority,target,0.0),self.id)
		op.setLinkable(linkable,mask,flag)
		return op

	def postMultInverseLinkable(self,linkable,mask=LINK_POS|LINK_ORI,flag=0,priority=0,target=LINK_FULL_OP):
		"""Add an operator that will post-multiply with the inverse matrix value of a linkable"""
		op = VizLinkableOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_POST_INV_LINKABLE,priority,target,0.0),self.id)
		op.setLinkable(linkable,mask,flag)
		return op

	def lookAtLinkable(self, linkable, flag=0, priority=0, target=LINK_FULL_OP):
		"""Add an operator that will rotate the matrix to look at the specified linkable position"""
		op = VizLookAtOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_LOOK_AT,priority,target,0.0),self.id)
		op.setLinkable(linkable,flag)
		return op

	def invert(self,priority=0,target=LINK_FULL_OP):
		op = VizInvertOperator(_ipcSend(_VIZ_LINKSET,self.id,_LINK_OPERATOR,'',_LINK_INVERT,priority,target,0.0),self.id)
		return op

class VizExtensionNode(VizNode):
	"""VizExtensionNode object"""
	def command(self, command = 0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0):
		"""Send a command to the extension node"""
		return _ipcSend(_VIZ_CMDEXTNODE,self.id,command,mesg,x,y,z,w)

class VizExtensionTexture(VizTexture):
	"""VizExtensionTexture object"""
	def command(self, command = 0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0):
		"""Send a command to the extension texture"""
		return _ipcSend(_VIZ_CMDEXTTEX,self.id,command,mesg,x,y,z,w)

class VizExtensionSensor(VizLinkable):
	"""VizExtensionSensor object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_EXT_SENSOR
	_VizLinkableType = _VIZ_EXTSENSOR_LINKABLE

	def __init__(self, id):
		VizLinkable.__init__(self, id)

	def remove(self):
		"""Remove the extension sensor"""
		if _ipcSend(_VIZ_DELEXTSENSOR,self.id,0,'',0.0,0.0,0.0,0.0):
			self.id = -1

	def command(self, command = 0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0):
		"""Send a command to the extension sensor"""
		return _ipcSend(_VIZ_CMDEXTSENSOR,self.id,command,mesg,x,y,z,w)

	def reset(self, command = 0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0):
		"""Send a reset command to the extension sensor"""
		return _ipcSend(_VIZ_RSTEXTSENSOR,self.id,command,mesg,x,y,z,w)

	def getData(self):
		"""Retrieve data from the extension sensor"""
		return _ipcSend(_VIZ_GETEXTSENSOR,-1,self.id,'',0.0,0.0,0.0,0.0)

	def getName(self):
		"""Return the name of the sensor"""
		return _ipcSend(_VIZ_GETEXTSENSOR,FILENAME,self.id,'',0.0,0.0,0.0,0.0)

	def getButtonCount(self):
		"""Return the number of buttons on the sensor"""
		return _ipcSend(_VIZ_GETEXTSENSOR,_BUTTON_COUNT,self.id,'',0.0,0.0,0.0,0.0)

	def getButtonState(self):
		"""Return the current state of the sensor buttons as a bit flag"""
		return _ipcSend(_VIZ_GETEXTSENSOR,_BUTTONS_STATE,self.id,'',0.0,0.0,0.0,0.0)

	def isButtonDown(self,button):
		"""Returns whether the specified button is currently down"""
		return _ipcSend(_VIZ_GETEXTSENSOR,_BUTTON_STATE,self.id,'',button,0.0,0.0,0.0)

	def _getSensor(self, command = 0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0, cls=None, **kw):
		"""Get access to children sensors"""
		id = _ipcSend(_VIZ_GETSENSORCHILD, self.id, command, mesg, x, y, z, w)
		sensor = VizExtensionSensor._VizObjectCache.get(id,None)
		if cls is None:
			cls = VizExtensionSensor
		if sensor is not None and sensor.__class__ is cls:
			return sensor
		return cls(id,**kw)

_GetExtSensor = DeprecateObject(VizExtensionSensor._GetObject)

class VizExtensionObject(VizObject):
	"""VizExtensionObject object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_EXT_OBJECT

	def __init__(self, id):
		VizObject.__init__(self, id)

	def remove(self):
		"""Permanently remove the extension object"""
		_ipcSend(_VIZ_DELEXTOBJECT,self.id,0,'',0.0,0.0,0.0,0.0)

	def command(self, command = 0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0):
		"""Send a command to the extension object"""
		return _ipcSend(_VIZ_CMDEXTOBJECT,self.id,command,mesg,x,y,z,w)

class VizExtension(VizObject):
	"""VizExtension object"""

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_EXTENSION

	def __init__(self, id):
		VizObject.__init__(self, id)
		self._nodeClass = VizExtensionNode
		self._textureClass = VizExtensionTexture
		self._sensorClass = VizExtensionSensor
		self._objectClass = VizExtensionObject

	def getName(self):
		"""Get the name of the extension object"""
		return _ipcSend(_VIZ_EXTGET,MESSAGE,self.id,'',0.0,0.0,0.0,0.0)

	def getFilename(self):
		"""Get the filename of the extension object"""
		return _ipcSend(_VIZ_EXTGET,FILENAME,self.id,'',0.0,0.0,0.0,0.0)

	def command(self,command=0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0):
		"""Send a command to the extension"""
		return _ipcSend(_VIZ_EXTCOMMAND,self.id,command,mesg,x,y,z,w)

	def addNode(self,command=0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0, parent = WORLD, scene = MainScene, cls=None, **kw):
		"""Add a node from the extension
		@return VizExtensionNode()"""
		_ipcSend(_VIZ_QUEUECOMMAND,0,command,mesg,x,y,z,w)
		if cls is None:
			cls = self._nodeClass
		return cls._GetObject(_ipcSend(_VIZ_ADDEXTNODE,self.id,_sceneID(scene),'',int(parent),0.0,0.0,0.0),**kw)

	def addTexture(self,command=0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0, cls=None, **kw):
		"""Add a texture from the extension
		@return VizExtensionTexture()"""
		if cls is None:
			cls = self._textureClass
		return cls._GetObject(_ipcSend(_VIZ_ADDEXTTEX,self.id,command,mesg,x,y,z,w),**kw)

	def addSensor(self,command=0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0, cls=None, **kw):
		"""Add a sensor from the extension
		@return VizExtensionSensor()"""
		id = _ipcSend(_VIZ_ADDEXTSENSOR,self.id,command,mesg,x,y,z,w)
		sensor = VizExtensionSensor._VizObjectCache.get(id,None)
		if cls is None:
			cls = self._sensorClass
		if sensor is not None and sensor.__class__ is cls:
			return sensor
		return cls(id,**kw)

	def addObject(self,command=0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0, cls=None, **kw):
		"""Add an object from the extension
		@return VizExtensionObject()"""
		id = _ipcSend(_VIZ_ADDEXTOBJECT,self.id,command,mesg,x,y,z,w)
		obj = VizExtensionObject._VizObjectCache.get(id,None)
		if cls is None:
			cls = self._objectClass
		if obj is not None and obj.__class__ is cls:
			return obj
		return cls(id,**kw)

	def modifyNode(self,node,command=0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0):
		"""Have the extension perform a modification on the node"""
		_ipcSend(_VIZ_QUEUECOMMAND,0,command,mesg,x,y,z,w)
		return _ipcSend(_VIZ_EXTMODNODE,self.id,node.id,'',0.0,0.0,0.0,0.0)

	def modifyTexture(self,tex,command=0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0):
		"""Have the extension perform a modification on the texture"""
		_ipcSend(_VIZ_QUEUECOMMAND,0,command,mesg,x,y,z,w)
		return _ipcSend(_VIZ_EXTMODTEX,self.id,tex.id,'',tex._textype,0.0,0.0,0.0)

	def modifyLinkable(self,linkable,command=0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0):
		"""Have the extension perform a modification on the linkable"""
		linkableType = _getLinkableType(linkable)
		if linkableType < 0:
			raise TypeError('Object is not a linkable')
		_ipcSend(_VIZ_QUEUECOMMAND,0,command,mesg,x,y,z,w)
		return _ipcSend(_VIZ_EXTMODLINKABLE,self.id,linkable.id,'',linkableType,0.0,0.0,0.0)

_GetExtension = VizExtension._GetObject

class VizPhysicsShape(VizObject):
	"""Physics shape object"""
	def __init__(self, id, node, pos=None, quat=None, euler=None, axisAngle=None, friction=None, density=None, hardness=None, bounce=None):
		VizObject.__init__(self, id)
		self.node = node

		#Set position
		if pos is not None:
			self.setPosition(pos)

		#Set rotation
		if quat is not None:
			self.setQuat(quat)
		if euler is not None:
			self.setEuler(euler)
		if axisAngle is not None:
			self.setAxisAngle(axisAngle)

		#Set friction
		if friction is not None:
			self.setFriction(friction)

		#Set density
		if density is not None:
			self.setDensity(density)

		#Set hardness
		if hardness is not None:
			self.setHardness(hardness)

		#Set bounce
		if bounce is not None:
			self.setBounce(bounce)

	def command(self, command = 0, mesg='', x = 0.0, y = 0.0, z = 0.0, w = 0.0):
		"""Send a custom command to the physics geometry object"""
		_ipcSend(_VIZ_QUEUEPHYSCMD,0,command,mesg,x,y,z,w)
		return _ipcSend(_VIZ_NODECMDPHYS,2,self.node,'',self.id,0.0,0.0,0.0)

	def getType(self):
		"""Get the shape type"""
		return _ipcSend(_VIZ_CHILDGET,_SHAPE_TYPE,self.node,'',self.id,0.0,0.0,0.0)

	def setMaterial(self,param,value):
		"""Set a material value for the physics geometry object"""
		_ipcSend(_VIZ_PHYSMATERIAL,self.node,self.id,'',param,value,0.0,0.0)

	def getMaterial(self,param):
		"""Get a material value from the object"""
		return _ipcSend(_VIZ_CHILDGET,_SHAPE_MATERIAL,self.node,'',self.id,param,0.0,0.0)

	def setFriction(self,value):
		"""Set friction of geometry"""
		self.setMaterial(_PHYSICS_FRICTION,value)

	def getFriction(self):
		"""Get friction of geometry"""
		return self.getMaterial(_PHYSICS_FRICTION)

	friction = property(getFriction,setFriction,doc='Friction of physics shape')

	def setDensity(self,value):
		"""Set density of geometry"""
		self.setMaterial(_PHYSICS_DENSITY,value)

	def getDensity(self):
		"""Get density of geometry"""
		return self.getMaterial(_PHYSICS_DENSITY)

	density = property(getDensity,setDensity,doc='Density of physics shape')

	def setHardness(self,value):
		"""Set hardness of geometry"""
		self.setMaterial(_PHYSICS_HARDNESS,value)

	def getHardness(self):
		"""Get hardness of geometry"""
		return self.getMaterial(_PHYSICS_HARDNESS)

	hardness = property(getHardness,setHardness,doc='Hardness of physics shape')

	def setBounce(self,value):
		"""Set bounciness of geometry"""
		self.setMaterial(_PHYSICS_BOUNCE,value)

	def getBounce(self):
		"""Get bounciness of geometry"""
		return self.getMaterial(_PHYSICS_BOUNCE)

	bounce = property(getBounce,setBounce,doc='Bounciness of physics shape')

	def setPosition(self,x,y=0,z=0):
		"""Set position of shape relative to node"""
		if _islist(x):
			_ipcSend(_VIZ_SETPHYSPOS,self.node,self.id,'',x[0],x[1],x[2],0.0)
		else:
			_ipcSend(_VIZ_SETPHYSPOS,self.node,self.id,'',x,y,z,0.0)

	def setQuat(self,x,y=0,z=0,w=0):
		"""Set quaternion rotation of shape relative to node"""
		if _islist(x):
			_ipcSend(_VIZ_SETPHYSROT,self.node,self.id,'',x[0],x[1],x[2],x[3])
		else:
			_ipcSend(_VIZ_SETPHYSROT,self.node,self.id,'',x,y,z,w)

	def setEuler(self,*args):
		"""Set euler rotation of shape relative to node"""
		self.setQuat(vizmat.EulerToQuat(*args))

	def setAxisAngle(self,*args):
		"""Set axis-angle rotation of shape relative to node"""
		self.setQuat(vizmat.AxisAngleToQuat(*args))

	def getPosition(self):
		"""Get position of shape relative to node"""
		return _ipcSend(_VIZ_CHILDGET,_SHAPE_POS,self.node,'',self.id,0.0,0.0,0.0)

	def getQuat(self):
		"""Get quaternion of shape relative to node"""
		return _ipcSend(_VIZ_CHILDGET,_SHAPE_ROT,self.node,'',self.id,0.0,0.0,0.0)

	def getEuler(self):
		"""Get euler of shape relative to node"""
		return vizmat.QuatToEuler(self.getQuat())

	def getAxisAngle(self):
		"""Get axis angle of shape relative to node"""
		return vizmat.QuatToAxisAngle(self.getQuat())

class VizPhysicsJoint(VizObject):
	"""Physics joint object"""
	def __init__(self, id, enabled=None, collide=None, pos=None, axis0=None, axis1=None, axis2=None, friction=None, hardness=None, bounce=None):
		VizObject.__init__(self, id)
		_AddJoint(self)

		if self.valid():
			if enabled is not None:
				self.setEnabled(enabled)
			if collide is not None:
				self.setCollide(collide)
			if pos is not None:
				self.setPosition(pos,True)
			if axis0 is not None:
				self.setAxis(0,axis0)
			if axis1 is not None:
				self.setAxis(1,axis1)
			if axis2 is not None:
				self.setAxis(2,axis2)
			if friction is not None:
				self.setAxisFriction(-1,friction)
			if hardness is not None:
				self.setAxisHardness(-1,hardness)
			if bounce is not None:
				self.setAxisBounce(-1,bounce)

	def remove(self):
		"""Permanently remove the joint"""
		_ipcSend(_VIZ_JOINTSET,self.id,1,'',0.0,0.0,0.0,0.0)
		_RemoveJoint(self.id)
		self.id = -1

	def reset(self):
		"""Reset nodes attached to solid"""
		_ipcSend(_VIZ_JOINTSET,self.id,6,'',0.0,0.0,0.0,0.0)

	def getNode1(self):
		"""Get first node attached to joint"""
		return _GetNode(_ipcSend(_VIZ_JOINTGET,self.id,10,'',0.0,0.0,0.0,0.0))

	def getNode2(self):
		"""Get second node attached to joint"""
		return _GetNode(_ipcSend(_VIZ_JOINTGET,self.id,11,'',0.0,0.0,0.0,0.0))

	def command(self,command=0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0):
		"""Send a custom command to the physics joint"""
		return _ipcSend(_VIZ_JOINTCOMMAND,self.id,command,mesg,x,y,z,w)

	def setEnabled(self,value):
		"""Set whether the joint is enabled"""
		_ipcSend(_VIZ_JOINTSET,self.id,0,'',value,0.0,0.0,0.0)

	def getEnabled(self):
		"""Get whether the joint is enabled"""
		return _ipcSend(_VIZ_JOINTGET,self.id,0,'',0.0,0.0,0.0,0.0)

	def enable(self):
		"""Enable the joint"""
		self.setEnabled(True)

	def disable(self):
		"""Disable the joint"""
		self.setEnabled(False)

	def setCollide(self,value):
		"""Set whether the objects connected by the joint can collide"""
		_ipcSend(_VIZ_JOINTSET,self.id,3,'',value,0.0,0.0,0.0)

	def getCollide(self):
		"""Get whether the object connected by the joint can collide"""
		return _ipcSend(_VIZ_JOINTGET,self.id,2,'',0.0,0.0,0.0,0.0)

	def setPosition(self,pos,reset=False):
		"""Set position of joint"""
		_ipcSend(_VIZ_JOINTSET,self.id,2,'',pos[0],pos[1],pos[2],reset)

	def getPosition(self):
		"""Get position of joint"""
		return _ipcSend(_VIZ_JOINTGET,self.id,1,'',0.0,0.0,0.0,0.0)

	def setAxis(self,num,vec):
		"""Set the direction vector of the joint axis"""
		_ipcSend(_VIZ_JOINTSET,self.id,4,'',vec[0],vec[1],vec[2],num)

	def getAxis(self,num):
		"""Get the direction vector of the joint axis"""
		return _ipcSend(_VIZ_JOINTGET,self.id,3,'',num,0.0,0.0,0.0)

	def _setAxisParam(self,num,param,value):
		"""Set a parameter value for the axis"""
		_ipcSend(_VIZ_JOINTSET,self.id,8,'',num,param,value,0.0)

	def _getAxisParam(self,num,param):
		"""Get a parameter value from the axis"""
		return _ipcSend(_VIZ_JOINTGET,self.id,9,'',num,param,0.0,0.0)

	def setAxisFriction(self,num,value): self._setAxisParam(num,_PHYSICS_FRICTION,value)
	def getAxisFriction(self,num): return self._getAxisParam(num,_PHYSICS_FRICTION)

	def setAxisHardness(self,num,value): self._setAxisParam(num,_PHYSICS_HARDNESS,value)
	def getAxisHardness(self,num): return self._getAxisParam(num,_PHYSICS_HARDNESS)

	def setAxisBounce(self,num,value): self._setAxisParam(num,_PHYSICS_BOUNCE,value)
	def getAxisBounce(self,num): return self._getAxisParam(num,_PHYSICS_BOUNCE)

	def getAxisAngle(self,num): return self._getAxisParam(num,_PHYSICS_AXIS_ANGLE)
	def getAxisDistance(self,num): return self._getAxisParam(num,_PHYSICS_AXIS_DIST)
	def getAxisVelocity(self,num): return self._getAxisParam(num,_PHYSICS_AXIS_VEL)

	def setAxisLimit(self,num,low=None,high=None):
		"""Set the limit of an axis"""
		if low is None:
			low = -1000000000.0
		if high is None:
			high = 1000000000.0
		_ipcSend(_VIZ_JOINTSET,self.id,5,'',num,low,high,0.0)

	def getAxisLimit(self,num):
		"""Get the limit of an axis"""
		return _ipcSend(_VIZ_JOINTGET,self.id,4,'',num,0.0,0.0,0.0)

	def setBreakMode(self,mode,breakThresh=0,accumThresh=0,removeBroken=True):
		"""Set the break mode of the joint"""
		_ipcSend(_VIZ_JOINTSET,self.id,7,'',mode,breakThresh,accumThresh,removeBroken)

	def getBreakMode(self):
		"""Get the break mode"""
		return _ipcSend(_VIZ_JOINTGET,self.id,5,'',0.0,0.0,0.0,0.0)

	def getBreakThresh(self):
		"""Get the break threshold"""
		return _ipcSend(_VIZ_JOINTGET,self.id,6,'',0.0,0.0,0.0,0.0)

	def getAccumThresh(self):
		"""Get the accumulate threshold"""
		return _ipcSend(_VIZ_JOINTGET,self.id,7,'',0.0,0.0,0.0,0.0)

	def getAccumDamage(self):
		"""Get the accumulated damage"""
		return _ipcSend(_VIZ_JOINTGET,self.id,8,'',0.0,0.0,0.0,0.0)

	"""OPAL specific functions:
		Motor functions are mutually exclusive per axis.
	"""
	def setMotorAngle(self, axis, angle, maxTorque = 1, speed = 0.1):
		"""Create a motor that will set the axis of the joint to the desired angle
		It will use up to 'maxTorque' to acheive the angle.
		'speed' is used to scale how fast the motor will acheive the angle"""
		self.command(1,'',axis,angle,maxTorque,speed)

	def setMotorVelocity(self, axis, velocity, maxTorque = 1):
		"""Create a motor that will set the axis of the joint to the desired velocity
		It will use up to 'maxTorque' to acheive the velocity."""
		self.command(2,'',axis,velocity,maxTorque)

	def setMotorThrottle(self, axis, throttle, maxTorque = 1, maxVelocity = 1):
		"""Create a motor to simulate an automobile engine.
		'maxTorque' is applied when angular velocity is zero.
		When the angular velocity reaches the 'maxVelocity', zero torque is applied.
		'throttle' must be between -1 and 1. 1 is max forward throttle, -1 is max reverse throttle, 0 is no throttle"""
		self.command(3,'',axis,throttle,maxTorque,maxVelocity)

	def disableMotor(self, axis):
		"""Disable the active motor on the axis"""
		self.command(4,'',axis)

class VizPhysicsHandler(object):

	def addJoint(self,jointType,node1,node2,**kw):
		"""Create a physics joint connecting the two nodes"""
		if node1 is None:
			node1 = -1
		if node2 is None:
			node2 = -1
		return VizPhysicsJoint(_ipcSend(_VIZ_PHYSADDJOINT,int(node1),int(node2),'',jointType,0.0,0.0,0.0),**kw)

	def addHingeJoint(self,*args,**kw):
		"""Create a hinge joint"""
		return self.addJoint(JOINT_HINGE,*args,**kw)

	def addWheelJoint(self,*args,**kw):
		"""Create a wheel joint"""
		return self.addJoint(JOINT_WHEEL,*args,**kw)

	def addUniversalJoint(self,*args,**kw):
		"""Create a universal joint"""
		return self.addJoint(JOINT_UNIVERSAL,*args,**kw)

	def addBallJoint(self,*args,**kw):
		"""Create a ball joint"""
		return self.addJoint(JOINT_BALL,*args,**kw)

	def addSliderJoint(self,*args,**kw):
		"""Create a slider joint"""
		return self.addJoint(JOINT_SLIDER,*args,**kw)

	def addFixedJoint(self,*args,**kw):
		"""Create a fixed joint"""
		return self.addJoint(JOINT_FIXED,*args,**kw)

	def command(self,command=0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0):
		"""Send a custom command to the physics simulator"""
		_ipcSend(_VIZ_QUEUEPHYSCMD,0,command,mesg,x,y,z,w)
		return _ipcSend(_VIZ_NODECMDPHYS,0,0,'',0.0,0.0,0.0,0.0)

	def setGravity(self,x,y=0,z=0):
		"""Set the gravity vector of the physics simulator"""
		if _islist(x):
			_ipcSend(_VIZ_PHYSGRAVITY,0,0,'',x[0],x[1],x[2],0.0)
		else:
			_ipcSend(_VIZ_PHYSGRAVITY,0,0,'',x,y,z,0.0)

	def getGravity(self):
		"""Get the gravity vector of the physics simulator"""
		return _ipcSend(_VIZ_PHYSICSGET,0,0,'',0.0,0.0,0.0,0.0)

	def intersectLine(self,begin,end,all=False):
		"""Intersect a line with the physics simulator.
		Returns a Intersect object
		@return Intersect()"""
		_ipcSend(_VIZ_SETLINEBEGIN,0,0,'',begin[0],begin[1],begin[2],0.0)

		return _ipcSend(_VIZ_PHYSICSGET,1,all,'',end[0],end[1],end[2],0.0)

	def intersectNode(self,node):
		"""Intersect a node with the physics simulator.
		The node must be added to the physics simulator.
		Returns a list of physics nodes that intersect this node"""
		vals = _ipcSend(_VIZ_PHYSICSGET,2,node.id,'',0.0,0.0,0.0,0.0)
		return [ _GetNode(id) for id in vals ]

	def setEnabled(self,val):
		"""Enable/Disable physics simulator"""
		_ipcSend(_VIZ_SETSCENEMODE,0,PHYSICS,'',val,0.0,0.0,0.0)

	def getEnabled(self):
		"""Return whether physics simulator is enabled"""
		return _ipcSend(_VIZ_PHYSICSGET,3,0,'',0.0,0.0,0.0,0.0)

	def enable(self):
		"""Enable physics"""
		self.setEnabled(True)

	def disable(self):
		"""Disable physics"""
		self.setEnabled(False)

	def setStepSize(self, seconds):
		"""Set the step size of the physics simulation"""
		self.command(1,'',seconds)

	def setAccuracy(self, level):
		"""Set the accuracy level of the physics simulation
		0 - VERY LOW
		1 - LOW
		2 - MEDIUM
		3 - HIGH
		4 - VERY HIGH"""
		self.command(2,'',level)

phys = VizPhysicsHandler()

def addExtension(filename, command=0, mesg = '', x = 0.0, y = 0.0, z = 0.0, w = 0.0, cls=None):
	"""Add a Vizard extension"""
	_beginAddExtension(filename)
	_ipcSend(_VIZ_QUEUECOMMAND,0,command,mesg,x,y,z,w)
	try:
		return createExtension(filename, _ipcSend(_VIZ_ADDEXTENSION,0,0,filename,0.0,0.0,0.0,0.0), cls)
	finally:
		_endAddExtension()

# Create static linkable objects
Mouse			= VizLinkable(0, _VIZ_MOUSE_LINKABLE)
NullLinkable	= VizLinkable(0, _VIZ_NULL_LINKABLE)

def _getLinkableType(obj):
	return getattr(obj, '_VizLinkableType', -1)

def _getLinkableObj(id,linkType):
	if linkType == _VIZ_NODE_LINKABLE:
		return VizNode._GetObject(id)
	elif linkType == _VIZ_VIEW_LINKABLE:
		return VizView._GetObject(id)
	elif linkType == _VIZ_SENSOR_LINKABLE:
		return VizSensor._GetObject(id)
	elif linkType == _VIZ_EXTSENSOR_LINKABLE:
		return VizExtensionSensor._GetObject(id)
	elif linkType == _VIZ_PATH_LINKABLE:
		return VizAnimationPath._GetObject(id)
	elif linkType == _VIZ_BONE_LINKABLE:
		return VizBone._GetObject(id)
	elif linkType == _VIZ_UNIFORM_LINKABLE:
		return VizUniform._GetObject(id)
	elif linkType == _VIZ_LINK_LINKABLE:
		return VizLink._GetObject(id)
	elif linkType == _VIZ_NULL_LINKABLE:
		return NullLinkable
	elif linkType == _VIZ_MOUSE_LINKABLE:
		return Mouse
	elif linkType == _VIZ_CUSTOM_LINKABLE:
		return VizCustomLinkable._GetObject(id)
	elif linkType == _VIZ_CONTROL_POINT_LINKABLE:
		return VizControlPoint._GetObject(id)
	elif linkType == _VIZ_SOUND_MIXER_LINKABLE:
		return VizSoundMixer._GetObject(id)
	return VizLinkable(id, linkType)

def mergeLinkable(pos,ori):
	"""Merge two linkable objects into one"""
	posType = _getLinkableType(pos)
	oriType = _getLinkableType(ori)

	if posType < 0:
		raise TypeError('Position linkable is not a linkable type')

	if oriType < 0:
		raise TypeError('Orientation linkable is not a linkable type')

	return VizMergeLinkable(_ipcSend(_VIZ_CREATELINKABLE,pos.id,ori.id,'',posType,oriType,0.0,0.0))

def flagWrappedLinkable(linkable,flag):
	"""Wraps get/set functions of linkable with specified flag"""
	linkableType = _getLinkableType(linkable)
	if linkableType < 0:
		raise TypeError('Object is not a linkable')
	return VizFlagWrappedLinkable(_ipcSend(_VIZ_CREATELINKABLE,linkable.id,linkableType,'',flag,0.0,0.0,2.0))

def blendLinkable(begin, end):
	"""Blend between two linkable objects by a specified blend amount"""
	beginType = _getLinkableType(begin)
	endType = _getLinkableType(end)

	if beginType < 0:
		raise TypeError('Begin linkable is not a linkable type')

	if endType < 0:
		raise TypeError('End linkable is not a linkable type')

	return VizBlendLinkable(_ipcSend(_VIZ_CREATELINKABLE,begin.id,end.id,'',beginType,endType,0.0,3.0))

def link(src,dst,priority=0,**kw):
	"""Link two objects together"""
	srcType = _getLinkableType(src)
	dstType = _getLinkableType(dst)

	if srcType < 0:
		raise TypeError('Link source is not a linkable type')

	if dstType < 0:
		raise TypeError('Link destination is not a linkable type')

	return VizLink(_ipcSend(_VIZ_LINKCREATE,src.id,dst.id,'',srcType,dstType,priority,0.0),**kw)

def grab(src,dst,absolute=False,srcFlag=None,dstFlag=None,**kw):
	"""Helper function that will create a link simulating the src object grabbing the dst object"""

	#Get current source pos/ori
	if srcFlag is None and absolute and isinstance(src,VizNode):
		src_pos = Vector(src.getPosition(ABS_GLOBAL))
		src_ori = Quat(src.getQuat(ABS_GLOBAL))
	elif srcFlag is not None:
		src_pos = Vector(src.getPosition(srcFlag))
		src_ori = Quat(src.getQuat(srcFlag))
	else:
		src_pos = Vector(src.getPosition())
		src_ori = Quat(src.getQuat())

	#Get current destination pos/ori
	if dstFlag is None and absolute and isinstance(dst,VizNode):
		dst_pos = Vector(dst.getPosition(ABS_GLOBAL))
		dst_ori = Quat(dst.getQuat(ABS_GLOBAL))
	elif dstFlag is not None:
		dst_pos = Vector(dst.getPosition(dstFlag))
		dst_ori = Quat(dst.getQuat(dstFlag))
	else:
		dst_pos = Vector(dst.getPosition())
		dst_ori = Quat(dst.getQuat())

	#link the objects
	ret = link(src,dst,srcFlag=srcFlag,dstFlag=dstFlag,**kw)

	if srcFlag is None and absolute and isinstance(src,VizNode):
		ret.setSrcFlag( ret.getSrcFlag() | ABS_GLOBAL )
	if dstFlag is None and absolute and isinstance(dst,VizNode):
		ret.setDstFlag( ret.getDstFlag() | ABS_GLOBAL )

	#Apply offset for orientation
	q = dst_ori * src_ori.inverse()
	ret.preQuat(q,target=LINK_ORI_OP)

	#Apply offset for position
	x = Transform()
	x.postQuat(dst_ori)
	x.postTrans((dst_pos-src_pos))
	x.postQuat(dst_ori.inverse())
	ret.preTrans(x.getTrans())

	return ret

def addAnimationPath(**kw):
	"""Add an animation path"""
	return VizAnimationPath(_ipcSend(_VIZ_ADDANIMPATH, 0, 0, '', 0.0, 0.0, 0.0, 0.0),**kw)

def addControlPoint(**kw):
	"""Add a control point"""
	return VizControlPoint(_ipcSend(_VIZ_ADDCTRLPOINT, 0, 0, '', 0.0, 0.0, 0.0, 0.0),**kw)

def addChild(filename, parent = WORLD, scene = MainScene, rotate=ROTATE_DEFAULT, cache=CACHE_DEFAULT, flags=0, **kw):
	"""Add a child to the scene
	@return VizChild()"""
	if _getFileExtension(filename).upper() in _TypeAvatar:
		return addAvatar(filename,parent=parent,scene=scene,flags=flags,**kw)
	flags = flags | max(0,rotate) | max(0,cache)
	return VizChild(_ipcSend(_VIZ_ADDCHILD, _sceneID(scene), int(parent), filename, flags, 0.0, 0.0, 0.0),**kw)

def addChildFromBuffer(filename, buffer, parent = WORLD, scene = MainScene, rotate=ROTATE_DEFAULT, flags=0, **kw):
	"""Add a model from a memory buffer"""

	flags = flags | max(0,rotate)

	#Get buffer
	buffer = _getBuffer(filename,buffer)

	_ipcSend(_VIZ_QUEUECOMMAND,0,0,filename,0.0,0.0,0.0,0.0)
	return VizChild(_ipcSend(_VIZ_ADDCHILDBUFFER, _sceneID(scene), int(parent), buffer, flags, 0.0, 0.0, 0.0),**kw)

def addCustomNode(filename, command = 0, mesg='', x = 0.0, y = 0.0, z = 0.0, w = 0.0, parent = WORLD, scene = MainScene, **kw):
	"""Add a custom child to the scene"""
	_ipcSend(_VIZ_ADDCUSTOM1,_sceneID(scene),0,filename,0.0,0.0,0.0,0.0)
	return createCustomNode(filename,_ipcSend(_VIZ_ADDCUSTOM2, int(parent), command, mesg, x, y, z, w),**kw)

def addGroup(parent = WORLD, scene = MainScene,**kw):
	"""Add a group node to the scene"""
	return VizGroup(_ipcSend(_VIZ_ADDGROUP, _sceneID(scene), int(parent), '', 0.0, 0.0, 0.0, 0.0),**kw)

def addTexQuad(parent = WORLD, scene = MainScene, size=0, **kw):
	"""Add a texquad to the scene"""
	if not _islist(size):
		size = [size, size]
	return VizTexQuad(_ipcSend(_VIZ_ADDTEXQUAD, _sceneID(scene), int(parent), '', size[0], size[1], 0.0, 0.0),**kw)

def addTexture(filename, type = AUTO_COMPUTE, useCache = 0, flags=0, **kw):
	"""Add a texture
	@return VizTexture()"""
	if useCache:
		flags = flags | CACHE_CLONE
	return VizTexture._GetObject(_ipcSend(_VIZ_ADDTEXTURE, type, flags, filename, 0.0, 0.0, 0.0, 0.0),**kw)

def addRenderTexture(size=[0,0,0], type = TEX_2D, format = TEX_RGBA, **kw):
	"""Add a render texture"""
	size = list(size) + [0] #Ensures size is at least 3 elements large
	return VizTexture(_ipcSend(_VIZ_ADDRENDERTEX, type, format, '', size[0], size[1], size[2], 0.0),**kw)

def addBlankTexture(size, type = TEX_2D, format = TEX_RGB,**kw):
	"""Add a blank texture that the user can modify"""
	s = list(size) + [1,1] #Ensures size is at least 3 elements large
	return VizTexture(_ipcSend(_VIZ_ADDBLANKTEX, type, format, '', s[0], s[1], s[2], 0.0),**kw)

def addTextureFromBuffer(filename, buffer, type = AUTO_COMPUTE, flags = 0, **kw):
	"""Add a texture from a memory buffer"""

	#Get buffer
	buffer = _getBuffer(filename,buffer)

	_ipcSend(_VIZ_SETSTRING,0,0,filename,0.0,0.0,0.0,0.0)
	return VizTexture(_ipcSend(_VIZ_ADDTEXBUFFER, type, flags, buffer, 0.0, 0.0, 0.0, 0.0),**kw)

def addEnvironmentMap(filename, faces=AUTO_COMPUTE, **kw):
	"""Add an environment map from the specified base filename"""

	# Split filename by extension
	head,tail = os.path.splitext(filename)

	# Determine naming format of cubemap faces
	if faces == AUTO_COMPUTE:
		for formats in ENVMAP_FORMATS:
			if res.getFullPath(head+formats[0]+tail):
				faces = formats
				break
		else:
			faces = ENVMAP_FORMATS[0]

	# Create cubemap texture and load file into each face
	envmap = addTexture(head+faces[0]+tail,type=TEX_CUBE,wrap=CLAMP_TO_EDGE)
	if envmap.valid():
		envmap.load(head+faces[1]+tail,NEGATIVE_X)
		envmap.load(head+faces[2]+tail,POSITIVE_Y)
		envmap.load(head+faces[3]+tail,NEGATIVE_Y)
		envmap.load(head+faces[4]+tail,POSITIVE_Z)
		envmap.load(head+faces[5]+tail,NEGATIVE_Z)

	return envmap

def addVideo(filename, type = TEX_2D, device=AUTO_COMPUTE, **kw):
	"""Add a video file"""
	return VizVideoTexture(_ipcSend(_VIZ_ADDVIDEOTEX, type, int(device), filename, 0.0, 0.0, 0.0, 0.0),**kw)

def addAudio(filename, device=AUTO_COMPUTE, **kw):
	"""Add an audio file"""
	return VizAudio(_ipcSend(_VIZ_ADDAUDIO, int(device), 0, filename,0.0,0.0,0.0,0.0),**kw)

def addSoundMixer(parent=None, device=AUTO_COMPUTE, flags=0):
	"""Add sound mixer object"""
	if parent is None:
		parent = -1
	return VizSoundMixer(_ipcSend(_VIZ_MIXERSET, 1, int(parent), '', int(device), 0.0, 0.0, 0.0))

def addText(value, parent = WORLD, scene = MainScene, **kw):
	"""Add 2d text to the scene"""
	return VizText(_ipcSend(_VIZ_ADDTEXT, _sceneID(scene), int(parent), value, 0, 0.0, 0.0, 0.0),**kw)

def addText3D(value, parent = WORLD, scene = MainScene, **kw):
	"""Add 3d text to the scene"""
	return VizText(_ipcSend(_VIZ_ADDTEXT, _sceneID(scene), int(parent), value, 1, 0.0, 0.0, 0.0),**kw)

def addLight(parent = WORLD, scene = MainScene, group=0, **kw):
	"""Add a light to the scene"""
	return VizLight(_ipcSend(_VIZ_ADDLIGHT,_sceneID(scene),int(parent),'',group,0.0,0.0,0.0),**kw)

def addDirectionalLight(*args,**kw):
	"""Add a directional light to the scene"""
	light = addLight(*args,**kw)
	light.position(0,0,-1,0)
	return light

def addPointLight(*args, **kw):
	"""Add a point light to the scene"""
	light = addLight(*args,**kw)
	light.position(0,0,0)
	return light

def addSpotLight(spread=45.0, *args, **kw):
	"""Add a spot light to the scene"""
	light = addLight(*args,**kw)
	light.position(0,0,0)
	light.direction(0,0,1)
	light.spread(spread)
	return light

def addMailbox(address):
	"""Add a mailbox"""
	return VizMailbox(_ipcSend(_VIZ_ADDMAIL,0,0,address,0.0,0.0,0.0,0.0))

def addAvatar(filename, parent = WORLD, scene = MainScene, flags=0, **kw):
	"""Add an avatar to the scene"""
	return VizAvatar(_ipcSend(_VIZ_ADDAVATAR, _sceneID(scene), int(parent), filename, flags, 0.0, 0.0, 0.0),**kw)

def addFace(filename, parent = WORLD, scene = MainScene,**kw):
	"""Add a face to the scene"""
	return VizFace(_ipcSend(_VIZ_ADDFACE, _sceneID(scene), int(parent), filename, 0.0, 0.0, 0.0, 0.0),**kw)

def addGUICanvas(parent = WORLD, scene = MainScene, **kw):
	"""Add a GUI canvas node to the scene"""
	return VizGUICanvas(_ipcSend(_VIZ_ADDGUIGROUP, _sceneID(scene), int(parent), '', 0.0, 0.0, 0.0, 1.0),**kw)

def addGUIGroup(parent = DEFAULT_CANVAS_SCREEN, scene = MainScene,**kw):
	"""Add a GUI group node to the scene"""
	return VizGUIObject(_ipcSend(_VIZ_ADDGUIGROUP, _sceneID(scene), int(parent), '', 0.0, 0.0, 0.0, 0.0),**kw)

def addCheckbox(scene = MainScene, parent = DEFAULT_CANVAS_SCREEN,**kw):
	"""Add a checkbox to the scene"""
	return VizCheckBox(_ipcSend(_VIZ_ADDCHECKBOX,_sceneID(scene),0,'',int(parent),0.0,0.0,0.0),**kw)

def addButton(scene = MainScene, parent = DEFAULT_CANVAS_SCREEN,**kw):
	"""Add a button to the scene"""
	return VizCheckBox(_ipcSend(_VIZ_ADDCHECKBOX,_sceneID(scene),1,'',int(parent),0.0,0.0,0.0),**kw)

def addRadioButton(group, scene = MainScene, parent = DEFAULT_CANVAS_SCREEN,**kw):
	"""Add a radio button to the scene"""
	return VizRadioButton(_ipcSend(_VIZ_ADDRADIOBUTTON,_sceneID(scene),int(parent),str(group),0.0,0.0,0.0,0.0),**kw)

def addSlider(scene = MainScene, parent = DEFAULT_CANVAS_SCREEN,**kw):
	"""Add a slider to the scene"""
	return VizSlider(_ipcSend(_VIZ_ADDSLIDER,_sceneID(scene),int(parent),'',0.0,0.0,0.0,0.0),**kw)

def addTextbox(scene = MainScene, parent = DEFAULT_CANVAS_SCREEN,**kw):
	"""Add a textbox to the scene"""
	return VizTextbox(_ipcSend(_VIZ_ADDTEXTBOX,_sceneID(scene),int(parent),'',0.0,0.0,0.0,0.0),**kw)

def addProgressBar(value, scene = MainScene, parent = DEFAULT_CANVAS_SCREEN,**kw):
	"""Add a progress bar to the scene"""
	return VizProgressBar(_ipcSend(_VIZ_ADDPROGRESSBAR,_sceneID(scene),int(parent),value,0.0,0.0,0.0,0.0),**kw)

def addButtonLabel(value, scene = MainScene, parent = DEFAULT_CANVAS_SCREEN,**kw):
	"""Add a button label to the scene"""
	return VizButtonLabel(_ipcSend(_VIZ_ADDBUTTONLABEL,_sceneID(scene),int(parent),value,1.0,0.0,0.0,0.0),**kw)

def addToggleButton(value, group='', scene = MainScene, parent = DEFAULT_CANVAS_SCREEN,**kw):
	"""Add a toggle button label to the scene"""
	_ipcSend(_VIZ_SETSTRING,0,0,str(group),0.0,0.0,0.0,0.0)
	return VizButtonLabel(_ipcSend(_VIZ_ADDBUTTONLABEL,_sceneID(scene),int(parent),value,0.0,0.0,0.0,0.0),**kw)

def addDropList(scene = MainScene, parent = DEFAULT_CANVAS_SCREEN,**kw):
	"""Add a drop list to the scene"""
	return VizDropList(_ipcSend(_VIZ_ADDDROPLIST,_sceneID(scene),int(parent),'',0.0,0.0,0.0,0.0),**kw)

def addTabGroup(scene = MainScene, parent = DEFAULT_CANVAS_SCREEN,**kw):
	"""Add a tab group to the scene"""
	return VizTabGroup(_ipcSend(_VIZ_ADDDROPLIST,_sceneID(scene),int(parent),'',0.0,0.0,0.0,1.0),**kw)

def addRenderNode(scene = MainScene, **kw):
	"""Add a render node to the scene"""
	return VizRenderNode(_ipcSend(_VIZ_ADDRENDERNODE,_sceneID(scene),0,'',0.0,0.0,0.0,0.0),**kw)

def addShader(flag=0,**kw):
	"""Add a shader program"""
	return VizShader(_ipcSend(_VIZ_ADDSHADER,flag,0,'',0.0,0.0,0.0,0.0),**kw)

def addUniform(name,dataType,arraySize=1):
	"""Add a shader uniform
	@return VizUniform()"""
	cls = {UNIFORM_FLOAT_MAT3:VizUniformMat3,UNIFORM_FLOAT_MAT4:VizUniformMat4}.get(dataType,VizUniform)
	return cls(_ipcSend(_VIZ_ADDUNIFORM,dataType,arraySize,name,0.0,0.0,0.0,0.0))

def addUniformBool(name,value,arraySize=1):
	"""Add a shader uniform containing bools"""
	if _islist(value):
		dataType = {1:UNIFORM_BOOL,2:UNIFORM_BOOL_VEC2,3:UNIFORM_BOOL_VEC3}.get(len(value),UNIFORM_BOOL_VEC4)
	else:
		dataType = UNIFORM_BOOL
	u = addUniform(name,dataType,arraySize)
	u.set(value)
	return u

def addUniformInt(name,value,arraySize=1):
	"""Add a shader uniform containing integers"""
	if _islist(value):
		dataType = {1:UNIFORM_INT,2:UNIFORM_INT_VEC2,3:UNIFORM_INT_VEC3}.get(len(value),UNIFORM_INT_VEC4)
	else:
		dataType = UNIFORM_INT
	u = addUniform(name,dataType,arraySize)
	u.set(value)
	return u

def addUniformFloat(name,value,arraySize=1):
	"""Add a shader uniform containing floats"""
	if _islist(value):
		dataType = {1:UNIFORM_FLOAT,2:UNIFORM_FLOAT_VEC2,3:UNIFORM_FLOAT_VEC3}.get(len(value),UNIFORM_FLOAT_VEC4)
	else:
		dataType = UNIFORM_FLOAT
	u = addUniform(name,dataType,arraySize)
	u.set(value)
	return u

def addUniformMatrix(name,value,arraySize=1):
	"""Add a shader uniform containing a matrix"""
	if len(value) >= 16:
		dataType = UNIFORM_FLOAT_MAT4
	elif len(value) >= 9:
		dataType = UNIFORM_FLOAT_MAT3
	elif len(value) >= 4:
		dataType = UNIFORM_FLOAT_MAT2
	else:
		raise ValueError('Not enough values for matrix type')

	u = addUniform(name,dataType,arraySize)
	u.set(value)
	return u

def addEffect(source, **kw):
	"""Add an effect object"""
	return VizEffect(_ipcSend(_VIZ_ADDEFFECT,1,0,source,0.0,0.0,0.0,0.0),**kw)

def addEffectComposer(source, **kw):
	"""Add an effect composer object"""
	return VizEffectComposer(_ipcSend(_VIZ_ADDEFFECT,2,0,source,0.0,0.0,0.0,0.0),**kw)

def addImageGen(filename, command = 0, mesg='', x = 0.0, y = 0.0, z = 0.0, w = 0.0):
	"""Add an ImageGen"""
	_ipcSend(_VIZ_INITPLUGIN,0,0,filename,0.0,0.0,0.0,0.0)
	return createImageGen(filename,_ipcSend(_VIZ_ADDIMAGEGEN,command,0,mesg,x,y,z,w))

def addModifier(filename):
	"""Add a modifier"""
	return createModifier(filename,_ipcSend(_VIZ_ADDMODIFIER,0,0,filename,0.0,0.0,0.0,0.0))

def addSensor(filename):
	"""Add a sensor"""
	return createSensor(filename,_ipcSend(_VIZ_ADDSENSOR,0,0,filename,0.0,0.0,0.0,0.0))

def addRenderer(filename, scene = MainScene):
	"""Add a renderer"""
	return VizRenderer(_ipcSend(_VIZ_ADDRENDERER,_sceneID(scene),0,filename,0.0,0.0,0.0,0.0))

def addScene(**kw):
	"""Add a scene"""
	return VizScene(_ipcSend(_VIZ_ADDSCENE,0,0,'',0.0,0.0,0.0,0.0),**kw)

def addView(**kw):
	"""Add a viewpoint"""
	return VizView(_ipcSend(_VIZ_ADDVIEW,0,0,'',0.0,0.0,0.0,0.0),**kw)

def addWindow(**kw):
	"""Add a window"""
	return VizWindow(_ipcSend(_VIZ_ADDWINDOW,0,0,'',0.0,0.0,0.0,0.0),**kw)

def addResourceContext(**kw):
	"""Add a resource context"""
	return VizResourceContext(_ipcSend(_VIZ_ADDRESCONTEXT,0,0,'',0.0,0.0,0.0,0.0),**kw)

def getCurrentResourceContext():
	"""Get the current resource context
	@return VizResourceContext()"""
	return VizResourceContext._GetObject(_ipcSend(_VIZ_RESCONTEXTGET,1,0,'',0.0,0.0,0.0,0.0))

def loadSound3D(file):
	"""Load a Sound3D engine"""
	_ipcSend(_VIZ_SOUND3DENGINE,0,0,file,0.0,0.0,0.0,0.0)

def commandSound3D(command,mesg='',x=0.0,y=0.0,z=0.0,w=0.0):
	"""Send a command to the Sound3D engine"""
	_ipcSend(_VIZ_SOUND3DENGINE,1,command,mesg,x,y,z,w)

def setListenerSound3D(listener,flag=0):
	"""Set the linkable object that represents the listener position for the Sound3D engine"""
	if listener is None:
		_ipcSend(_VIZ_SOUND3DENGINE,3,0,'',0.0,0.0,0.0,0.0)
	else:
		listenerType = _getLinkableType(listener)

		if listenerType < 0:
			raise TypeError('Listener object is not a linkable type')

		_ipcSend(_VIZ_SOUND3DENGINE,2,flag,'',listener.id,listenerType,0.0,0.0)

def setDebugSound3D(mode):
	"""Set debugging mode 3D sound objects. When enabled, icons will appear at the location of all playing 3D sounds"""
	_ipcSend(_VIZ_SOUND3DENGINE,4,mode,'',0.0,0.0,0.0,0.0)

def callback(event, function, mask = MASTER, priority = PRIORITY_DEFAULT):
	"""Create a callback for the given event type with the given function."""
	_ipcSendCallback(event,function,mask,0,priority)

def starttimer(timer=1, time=FASTEST_EXPIRATION, repeats=0):
	"""timer is the timer number that is passed back to your timer function
	time is the number of seconds to wait until the event is triggered
	repeats is the number of how many times this timer should repeat"""
	_ipcSend(_VIZ_STARTTIMER,timer,repeats,'',time,0,0.0,0.0)

def killtimer(timer):
	"""Kill all timers with ID equal to 'timer'"""
	_ipcSend(_VIZ_KILLTIMER,timer,0,'',0.0,0.0,0.0,0.0)

_vizPaused = False
def getPaused():
	"""Return whether timers are paused"""
	return _vizPaused

def pause():
	"""Pause all timers"""
	global _vizPaused
	_vizPaused = True
	_ipcSend(_VIZ_PAUSETIMERS,1,0,'',0.0,0.0,0.0,0.0)

def play():
	"""Resume all timers"""
	global _vizPaused
	_vizPaused = False
	_ipcSend(_VIZ_PAUSETIMERS,0,0,'',0.0,0.0,0.0,0.0)

def elapsed():
	"""Return elapsed timer of current expired timer"""
	return _ipcSend(_VIZ_TIMERELAPSED,0,0,'',0.0,0.0,0.0,0.0)

def getInputTime():
	"""Return time of last input event"""
	return _ipcSend(_VIZ_GET,_INPUT_TIME,0,'',0.0,0.0,0.0,0.0)

def playSound(filename = "", flag = 0):
	"""playsound(filename,flag=0)
	play the wav file specified by 'filename'
	Optional parameter 'flag' can be viz.LOOP"""
	_ipcSend(_VIZ_PLAYSOUND,flag,0,filename,0.0,0.0,0.0,0.0)

class AudioDevice(object):
	"""Class continaing information about an audio device"""
	def __init__(self, id, name, primary, channel_count, channel_mask):
		self.id = id
		self.name = name
		self.primary = primary
		self.channel_count = channel_count
		self.channel_mask = channel_mask

	def __int__(self):
		return self.id

	def __repr__(self):
		return 'AudioDevice(id={id}, name={name!r}, primary={primary}, channel_count={channel_count}, channel_mask={channel_mask})'.format(**self.__dict__)

def getAudioDeviceList():
	"""Get list of audio devices"""
	devices = []
	setOption('viz.audio.update_devices',None)
	device_count = getOption('viz.audio.device_count',0,type=int)
	device_primary = getOption('viz.audio.device_primary',1,type=int)
	for num in range(1,device_count+1):
		name = getOption('viz.audio.device_{}.name'.format(num))
		channel_count = getOption('viz.audio.device_{}.channel_count'.format(num),0,type=int)
		channel_mask = getOption('viz.audio.device_{}.channel_mask'.format(num),0,type=int)
		devices.append(AudioDevice(num, name, num==device_primary, channel_count, channel_mask))
	return devices

def setDefaultAudioDevice(device):
	"""Set the default audio device to use for all subsequent audio commands"""
	if device is None:
		device = 0
	elif isinstance(device, AudioDevice):
		device = device.id
	else:
		device = int(device)
	setOption('viz.audio.device', device)

#Quick access to main scene functions
intersect		= MainScene.intersect

#Quick access to main window functions
clearcolor		= MainWindow.clearcolor
clip			= MainWindow.clip
fov				= MainWindow.fov
pick			= MainWindow.pick
ipd				= MainWindow.ipd

def getRadioGroups():
	"""Get a list of all radio button groups"""
	result = _ipcSend(_VIZ_GET,_RADIO_GROUPS,0,'',0.0,0.0,0.0,0.0)
	return [ RadioGroup(name) for name in result ]

def getRadioButtons(groupName):
	"""Get a list of all radio buttons belonging to a group"""
	result = _ipcSend(_VIZ_GET,_RADIO_BUTTONS,0,groupName,0.0,0.0,0.0,0.0)
	return [ _GetNode(val) for val in result ]

def getSelectedRadio(groupName):
	"""Get the selected button of a radio group"""
	return _GetNode(_ipcSend(_VIZ_GET,_SELECTED_RADIO,0,groupName,0.0,0.0,0.0,0.0))

def setLightGroup(group):
	"""Set the active light group"""
	_ipcSend(_VIZ_LIGHTSHOW,group,0,'',1.0,0.0,0.0,0.0)

def getLightGroup():
	"""Get the active light group"""
	return _ipcSend(_VIZ_GET,_LIGHT_GROUP,0,'',0.0,0.0,0.0,0.0)

def setTagRender(tags, mode):
	"""Set default render mode for tag"""
	if _islist(tags):
		tags = _NAME_DELIMETER.join(tags)
	_ipcSend(_VIZ_SETTAGRENDER, 0, mode, tags, 0.0, 0.0, 0.0, 2.0)

def getTagRender(tag):
	"""Get default render mode for tag"""
	return _ipcSend(_VIZ_GET,_TAG_DEFAULT_RENDER,0,tag,0.0,0.0,0.0,0.0)

def startLayer(type,name=''):
	"""Begin an On-The-Fly object"""
	_ipcSend(_VIZ_STARTLAYER,type,0,name,0.0,0.0,0.0,0.0)

def endLayer(parent = WORLD, scene = MainScene,**kw):
	"""End an On-The-Fly object and return it"""
	return VizPrimitive(_ipcSend(_VIZ_ENDLAYER,_sceneID(scene),int(parent),'',0.0,0.0,0.0,0.0),**kw)

def vertex(x,y=0,z=0):
	"""Set a vertex position for an On-The-Fly object"""
	if _islist(x):
		_ipcSend(_VIZ_VERTEX,0,0,'',x[0],x[1],x[2],0.0)
	else:
		_ipcSend(_VIZ_VERTEX,0,0,'',x,y,z,0.0)

def normal(x,y=0,z=0):
	"""Set a normal vector for an On-The-Fly object"""
	if _islist(x):
		_ipcSend(_VIZ_NORMAL,0,0,'',x[0],x[1],x[2],0.0)
	else:
		_ipcSend(_VIZ_NORMAL,0,0,'',x,y,z,0.0)

def texCoord(x,y=0,z=0,unit=0):
	"""Set the texture coordinate for an On-The-Fly object"""
	if _islist(x):
		if len(x) < 3:
			_ipcSend(_VIZ_TEXCOORD,unit,0,'',x[0],x[1],0.0,0.0)
		else:
			_ipcSend(_VIZ_TEXCOORD,unit,0,'',x[0],x[1],x[2],0.0)
	else:
		_ipcSend(_VIZ_TEXCOORD,unit,0,'',x,y,z,0.0)

def vertexColor(r,g=1,b=0,a=1):
	"""Set a vertex color for an On-The-Fly object"""
	if _islist(r):
		if len(r) < 4:
			_ipcSend(_VIZ_VERTEXCOLOR,0,0,'',r[0],r[1],r[2],g)
		else:
			_ipcSend(_VIZ_VERTEXCOLOR,0,0,'',r[0],r[1],r[2],r[3])
	else:
		_ipcSend(_VIZ_VERTEXCOLOR,0,0,'',r,g,b,a)

def lineWidth(width):
	"""Set the line width for an On-The-Fly object"""
	_ipcSend(_VIZ_LINEWIDTH,0,0,'',width,0.0,0.0,0.0)

def pointSize(size):
	"""Set the point size for an On-The-Fly object"""
	_ipcSend(_VIZ_POINTSIZE,0,0,'',size,0.0,0.0,0.0)

def vsync(mode):
	"""Set vertical sync mode"""
	_ipcSend(_VIZ_SETVSYNC,mode,0,'',0.0,0.0,0.0,0.0)

###################################################################
######################## CAMERA INTERFACE #########################
###################################################################

class _CameraInterface(object):

	def setHandler(self,handler):
		"""Set the handler for manipulating the active viewpoint"""
		return _ipcSendCameraHandler(handler)

	def setReset(self):
		"""Use the current settings of the active camera as the reset values"""
		_ipcSend(_VIZ_RESETCAMERA,1,0,'',0.0,0.0,0.0,0.0)

	def reset(self):
		"""Reset the active camera handler"""
		_ipcSend(_VIZ_RESETCAMERA,0,0,'',0.0,0.0,0.0,0.0)

	def setView(self,view):
		"""Set the view used for camera handlers"""
		if view is None:
			_ipcSend(_VIZ_RESETCAMERA,2,-1,'',0.0,0.0,0.0,0.0)
		else:
			_ipcSend(_VIZ_RESETCAMERA,2,int(view),'',0.0,0.0,0.0,0.0)

	def getView(self):
		"""Get the view that is currently being used by the camera handler"""
		return VizView._GetObject(_ipcSend(_VIZ_RESETCAMERA,3,0,'',0.0,0.0,0.0,0.0))

cam = _CameraInterface()

###################################################################
######################## CLUSTER INTERFACE ########################
###################################################################

_clustered = False
_ClusterStack = []

class _ClusterInterface(object):
	"""For internal use only"""

	class ObserverClient(VizUser):

		def __init__(self, id, clientID):
			VizUser.__init__(self,id)
			self._clientID = clientID

		def getClientID(self):
			"""Return the observer client ID"""
			return self._clientID

	def __init__(self):
		master_id = _ipcSend(_VIZ_CLUSTERGET,11,0,'',0.0,0.0,0.0,0.0)
		self.Master = VizUser._GetObject(master_id if master_id is not None else -1)

	def __bool__(self):
		return _clustered

	@property
	def id(self):
		"""Returns cluster ID of this process"""
		return _ipcSend(_VIZ_CLUSTERGET,8,0,'',0.0,0.0,0.0,0.0)

	def isClient(self):
		"""Returns whether this process is running as a cluster client"""
		return self.id > MASTER

	def getObserverClientMask(self):
		"""Returns the mask of all observer clients"""
		return _ipcSend(_VIZ_CLUSTERGET,9,0,'',0.0,0.0,0.0,0.0)

	def getObserverClientList(self):
		"""Returns list of all observer client objects"""
		clients = _ipcSend(_VIZ_CLUSTERGET,10,0,'',0.0,0.0,0.0,0.0)
		return [ _ClusterInterface.ObserverClient._GetObject(userID,clientID) for clientID, userID in clients ]

	def getObserverClient(self, id):
		"""Get observer client from ID
		@return _ClusterInterface.ObserverClient()"""
		userID = _ipcSend(_VIZ_CLUSTERGET,12,id,'',0.0,0.0,0.0,0.0)
		return _ClusterInterface.ObserverClient._GetObject(userID,id)

	def setMask(self, mask):
		"""Set the mask for specifying which clients a command will be sent to"""
		return _ipcSendEx( 5 , mask )

	def getMask(self):
		"""Get current cluster mask"""
		return _ipcSend(_VIZ_CLUSTERGET,0,0,'',0.0,0.0,0.0,0.0)

	def _pushMaskDummy(self, mask):
		"""Save the current cluster mask and set it to the new value"""
		return

	def _popMaskDummy(self):
		"""Restore the cluster mask to the previous value"""
		return

	def _pushMaskReal(self, mask):
		"""Save the current cluster mask and set it to the new value"""
		_ClusterStack.append(self.setMask(mask))

	def _popMaskReal(self):
		"""Restore the cluster mask to the previous value"""
		self.setMask(_ClusterStack.pop())

	def getClientID(self, name):
		"""Returns the ID of a client given its name"""
		return _ipcSend(_VIZ_CLUSTERGET,2,0,name,0.0,0.0,0.0,0.0)

	def getClientName(self, id):
		"""Returns the name of a client given its ID"""
		return _ipcSend(_VIZ_CLUSTERGET,3,id,'',0.0,0.0,0.0,0.0)

	def getClient(self):
		"""Returns the client that triggered the current event"""
		return _ipcSend(_VIZ_CLUSTERGET,1,0,'',0.0,0.0,0.0,0.0)

	def flush(self):
		"""Flush queued up cluster messages to clients"""
		_ipcSend(_VIZ_CLUSTERGET,4,0,'',0.0,0.0,0.0,0.0)

	def setQueue(self,val):
		"""Set whether cluster messages will be queued"""
		_ipcSend(_VIZ_CLUSTERGET,5,val,'',0.0,0.0,0.0,0.0)

	def getQueue(self):
		"""Get whether cluster messages will be queued"""
		return _ipcSend(_VIZ_CLUSTERGET,6,0,'',0.0,0.0,0.0,0.0)

	class MaskedContext(object):
		"""Class that implements context manager protocol for pushing/popping a cluster mask"""
		def __init__(self,mask):
			self.mask = mask
			self._stack = []

		def __enter__(self):
			self._stack.append( _ipcSendEx( 5 , self.mask ) )

		def __exit__(self,exc_type, exc_val, exc_tb):
			_ipcSendEx( 5 , self._stack.pop() )

	class MaskedObject(object):
		"""A class that will wrap all function calls of an object with a cluster mask"""
		class _MaskedFunc(object):
			def __init__(self,func,mask):
				self.func = func
				self.mask = mask

			def __call__(self,*args,**kw):
				previous = _ipcSendEx( 5 , self.mask )
				try:
					return self.func(*args,**kw)
				finally:
					_ipcSendEx( 5 , previous )

		def __init__(self,obj,mask):
			self._MaskedObject_obj = obj
			self._MaskedObject_mask = mask

		def __getattr__(self,name):
			val = getattr(self._MaskedObject_obj,name)
			if callable(val):
				return self._MaskedFunc(val,self._MaskedObject_mask)
			return val

cluster = _ClusterInterface()

if getOption('viz.cluster') == '1':

	#Set global cluster flag to true
	_clustered = True

	#Set "viz.cluster.pushMask" and "viz.cluster.popMask" to real functions
	cluster.pushMask = cluster._pushMaskReal
	cluster.popMask = cluster._popMaskReal

else:

	#Set "viz.cluster.pushMask" and "viz.cluster.popMask" to dummy functions
	cluster.pushMask = cluster._pushMaskDummy
	cluster.popMask = cluster._popMaskDummy

MaskedObject = DeprecateObject(cluster.MaskedObject)

###############################################################
######################## KEY INTERFACE ########################
###############################################################

class _KeyInterface(object):
	"""For internal use only"""
	def isDown(self,key,immediate=0):
		"""Returns whether the given key is currently down"""
		if isinstance(key,str) and len(key) == 1:
			return _ipcSend(_VIZ_ISKEYDOWN,1,ord(key),'',immediate,0.0,0.0,0.0)
		return _ipcSend(_VIZ_ISKEYDOWN,1,int(key),'',immediate,0.0,0.0,0.0)

	def anyDown(self,keys,immediate=0):
		"""Returns whether any key in the list 'keys' is currently down"""
		for k in keys:
			if self.isDown(k,immediate):
				return True
		return False

	def allDown(self,keys,immediate=0):
		"""Returns whether all keys in the list 'keys' are currently down"""
		for k in keys:
			if not self.isDown(k,immediate):
				return False
		return True

	def charToCode(self,key):
		"""Convert the specified character to the Windows key code"""
		if isinstance(key,str) and len(key) == 1:
			return _ipcSend(_VIZ_ISKEYDOWN,2,ord(key),'',0.0,0.0,0.0,0.0)
		return _ipcSend(_VIZ_ISKEYDOWN,2,int(key),'',0.0,0.0,0.0,0.0)

	def codeToChar(self,key):
		"""Converts the Windows key code to the character representation"""
		return _ipcSend(_VIZ_ISKEYDOWN,3,key,'',0.0,0.0,0.0,0.0)

key = _KeyInterface()

#################################################################
######################## MOUSE INTERFACE ########################
#################################################################

class _MouseInterface(object):
	"""For internal use only"""

	class _Cursor(object):
		def __init__(self, resourceId):
			self.resourceId = resourceId

	# Standard system cursors
	CURSOR_APPSTARTING		= _Cursor(32650)
	CURSOR_ARROW			= _Cursor(32512)
	CURSOR_CROSS			= _Cursor(32515)
	CURSOR_HAND				= _Cursor(32649)
	CURSOR_HELP				= _Cursor(32651)
	CURSOR_IBEAM			= _Cursor(32513)
	CURSOR_NO				= _Cursor(32648)
	CURSOR_SIZEALL			= _Cursor(32646)
	CURSOR_SIZENESW			= _Cursor(32643)
	CURSOR_SIZENS			= _Cursor(32645)
	CURSOR_SIZENWSE			= _Cursor(32642)
	CURSOR_SIZEWE			= _Cursor(32644)
	CURSOR_UPARROW			= _Cursor(32516)
	CURSOR_WAIT				= _Cursor(32514)

	def getState(self,immediate=0):
		"""Returns the current state of the mouse buttons"""
		return _ipcSend(_VIZ_MOUSEGET,2,immediate,'',0.0,0.0,0.0,0.0)

	def getPosition(self,mode=WINDOW_NORMALIZED,immediate=0):
		"""Returns the current position of the mouse"""
		return _ipcSend(_VIZ_MOUSEGET,1,mode,'',immediate,0.0,0.0,0.0)

	def setVisible(self,state):
		"""Shows or Hides the mouse cursor"""
		_ipcSend(_VIZ_MOUSESET,3,state,'',0.0,0.0,0.0,0.0)

	def getVisible(self):
		"""Get visible state of mouse cursor"""
		return _ipcSend(_VIZ_MOUSEGET,3,0,'',0.0,0.0,0.0,0.0)

	def setAutoHideDelay(self, seconds):
		"""Set the auto hide delay of the mouse cursor, in seconds"""
		_ipcSend(_VIZ_MOUSESET,8,0,'',seconds,0.0,0.0,0.0)

	def getAutoHideDelay(self):
		"""Get the auto hide delay of the mouse cursor, in seconds"""
		return _ipcSend(_VIZ_MOUSEGET,8,0,'',0.0,0.0,0.0,0.0)

	def setTrap(self,state = ON):
		"""Set trap state of mouse"""
		_ipcSend(_VIZ_MOUSESET,4,state,'',0.0,0.0,0.0,0.0)

	def getTrap(self):
		"""Get trap state of mouse"""
		return _ipcSend(_VIZ_MOUSEGET,4,0,'',0.0,0.0,0.0,0.0)

	def setOverride(self,state = ON):
		"""Override mouse navigation control"""
		_ipcSend(_VIZ_MOUSESET,5,state,'',0.0,0.0,0.0,0.0)

	def getOverride(self):
		"""Get whether mouse override is enabled"""
		return _ipcSend(_VIZ_MOUSEGET,5,0,'',0.0,0.0,0.0,0.0)

	def setScale(self, moving, turning):
		"""Set the moving/turning scaling factor for mouse navigation"""
		_ipcSend(_VIZ_MOUSESET,6,0,'',moving,turning,0.0,0.0)

	def getScale(self):
		"""Get the moving/turning scaling factor for mouse navigation"""
		return _ipcSend(_VIZ_MOUSEGET,6,0,'',0.0,0.0,0.0,0.0)

	def setCursor(self, cursor):
		"""Set the mouse cursor"""
		if isinstance(cursor, str):
			return _ipcSend(_VIZ_MOUSESET,9,0,cursor,0.0,0.0,0.0,0.0)
		if isinstance(cursor, _MouseInterface._Cursor):
			return _ipcSend(_VIZ_MOUSESET,10,cursor.resourceId,'',0.0,0.0,0.0,0.0)
		return _ipcSend(_VIZ_MOUSESET,7,cursor,'',0.0,0.0,0.0,0.0)

	def getCursor(self):
		"""Get the mouse cursor"""
		return _ipcSend(_VIZ_MOUSEGET,7,0,'',0.0,0.0,0.0,0.0)

	def __call__(self, *args, **kwargs):
		#For backwards compatibility
		MainWindow.mouse(*args,**kwargs)

mouse = _MouseInterface()

##################################################################
######################## WINDOW INTERFACE ########################
##################################################################

class _WindowInterface(object):
	"""For internal use only"""

	class MonitorInfo(object):
		"""Class continaing information about a single monitor"""
		def __init__(self,id,name,position,size,primary):
			self.id = id
			self.name = name
			self.position = tuple(position)
			self.size = tuple(size)
			self.primary = primary

		def __repr__(self):
			return 'MonitorInfo(id={id}, name={name!r}, position={position}, size={size}, primary={primary})'.format(**self.__dict__)

	def getMonitorList(self):
		"""Get a list of currently active monitors"""
		monitors = []
		monitor_count = getOption('viz.monitor.count',0,type=int)
		primary_monitor = getOption('viz.monitor.primary',0,type=int)
		for num in range(monitor_count):
			name = getOption('viz.monitor_{}.name'.format(num))
			id = getOption('viz.monitor_{}.id'.format(num),0,type=int)
			x,y,width,height = [ int(value) for value in getOption('viz.monitor_{}.rectangle'.format(num)).split() ]
			monitors.append(self.MonitorInfo(id,name,[x,y],[width,height],id==primary_monitor))
		return monitors

	def getHandle(self):
		"""Get handle to graphics window"""
		return _ipcSend(_VIZ_DISPLAYGET,1,0,'',0.0,0.0,0.0,0.0)

	def getContext(self):
		"""Get handle to graphics context"""
		return _ipcSend(_VIZ_DISPLAYGET,20,0,'',0.0,0.0,0.0,0.0)

	def setFullscreen(self, mode = ON):
		"""Set whether window is in fullscreen mode"""
		_ipcSend(_VIZ_DISPLAYSET,2,mode,'',0.0,0.0,0.0,0.0)

	def getFullscreen(self):
		"""Return whether the display window is in fullscreen mode"""
		return _ipcSend(_VIZ_DISPLAYGET,2,0,'',0.0,0.0,0.0,0.0)

	def setFullscreenMonitor(self, monitor):
		"""Set the fullscreen size to the specified monitor dimensions"""
		if _islist(monitor):
			_ipcSend(_VIZ_DISPLAYSET,21,0,' '.join(str(int(x)) for x in monitor),0.0,0.0,0.0,0.0)
		elif isinstance(monitor, str):
			_ipcSend(_VIZ_DISPLAYSET,20,0,monitor,0.0,0.0,0.0,0.0)
		elif isinstance(monitor, _WindowInterface.MonitorInfo):
			_ipcSend(_VIZ_DISPLAYSET,18,monitor.id,'',0.0,0.0,0.0,0.0)
		else:
			_ipcSend(_VIZ_DISPLAYSET,18,monitor,'',0.0,0.0,0.0,0.0)

	def getFullscreenMonitor(self):
		"""Get the monitor used for fullscreen mode"""
		return _ipcSend(_VIZ_DISPLAYGET,18,0,'',0.0,0.0,0.0,0.0)

	def setFullscreenRectangle(self,rect):
		"""Set the [x,y,width,height] rectangle for fullscreen mode"""
		_ipcSend(_VIZ_DISPLAYSET,19,0,'',rect[0],rect[1],rect[2],rect[3])

	def getFullscreenRectangle(self):
		"""Get the [x,y,width,height] rectangle for fullscreen mode"""
		return _ipcSend(_VIZ_DISPLAYGET,19,0,'',0.0,0.0,0.0,0.0)

	def setSize(self, width, height=-1):
		"""Set the size of the graphics window"""
		if _islist(width):
			_ipcSend(_VIZ_DISPLAYSET,3,0,'',width[0],width[1],0.0,0.0)
		else:
			_ipcSend(_VIZ_DISPLAYSET,3,0,'',width,height,0.0,0.0)

	def getSize(self):
		"""Get size of window"""
		return _ipcSend(_VIZ_DISPLAYGET,3,0,'',0.0,0.0,0.0,0.0)

	def setPosition(self, x, y=0):
		"""Set the position of the graphics window (aligned to upper left corner)"""
		if _islist(x):
			_ipcSend(_VIZ_DISPLAYSET,4,0,'',x[0],x[1],0.0,0.0)
		else:
			_ipcSend(_VIZ_DISPLAYSET,4,0,'',x,y,0.0,0.0)

	def getPosition(self):
		"""Get position of display window"""
		return _ipcSend(_VIZ_DISPLAYGET,4,0,'',0.0,0.0,0.0,0.0)

	def setBorder(self, mode):
		"""Set the border mode of the graphics window"""
		_ipcSend(_VIZ_DISPLAYSET,5,mode,'',0.0,0.0,0.0,0.0)

	def getBorder(self):
		"""Get the border mode of the graphics window"""
		return _ipcSend(_VIZ_DISPLAYGET,5,0,'',0.0,0.0,0.0,0.0)

	def setFloat(self, mode = ON):
		"""Make the graphical window stay on top of all other windows"""
		_ipcSend(_VIZ_DISPLAYSET,6,mode,'',0.0,0.0,0.0,0.0)

	def getFloat(self):
		"""Get float state of graphics window"""
		return _ipcSend(_VIZ_DISPLAYGET,6,0,'',0.0,0.0,0.0,0.0)

	def setName(self, name):
		"""Set the name of the graphics window"""
		_ipcSend(_VIZ_DISPLAYSET,7,0,name,0.0,0.0,0.0,0.0)

	def getName(self):
		"""Get the name of the graphics window"""
		return _ipcSend(_VIZ_DISPLAYGET,7,0,'',0.0,0.0,0.0,0.0)

	def setFrameRate(self, mode = 1):
		"""Set frame rate display mode"""
		_ipcSend(_VIZ_DISPLAYSET,8,mode,'',0.0,0.0,0.0,0.0)

	def getFrameRate(self):
		"""Get frame rate display mode"""
		return _ipcSend(_VIZ_DISPLAYGET,8,0,'',0.0,0.0,0.0,0.0)

	def setPolyMode(self, mode):
		"""Set the polygon render mode"""
		_ipcSend(_VIZ_DISPLAYSET,9,mode,'',0.0,0.0,0.0,0.0)

	def getPolyMode(self):
		"""Get the polygon render mode"""
		return _ipcSend(_VIZ_DISPLAYGET,9,0,'',0.0,0.0,0.0,0.0)

	def screenCapture(self, filename, flags=0):
		"""Captures the current screen to the given image filename or texture object"""
		if isinstance(filename,VizTexture):
			_ipcSend(_VIZ_DISPLAYSET,17,0,'',filename.id,filename._textype,flags,0.0)
		else:
			_ipcSend(_VIZ_DISPLAYSET,10,0,filename,flags,0.0,0.0,0.0)

	def startRecording(self, filename):
		"""Start recording screen to AVI"""
		_ipcSend(_VIZ_DISPLAYSET,11,0,filename,0.0,0.0,0.0,0.0)

	def stopRecording(self):
		"""Stop recording screen to AVI"""
		_ipcSend(_VIZ_DISPLAYSET,12,0,'',0.0,0.0,0.0,0.0)

	def toggleRecording(self, filename='vizcapture.avi'):
		"""Toggle recording screen to AVI"""
		_ipcSend(_VIZ_DISPLAYSET,13,0,filename,0.0,0.0,0.0,0.0)

	def getRecording(self):
		"""Get whether recording is in progress"""
		return _ipcSend(_VIZ_DISPLAYGET,10,0,'',0.0,0.0,0.0,0.0)

	def displayHTML(self, filename = 'vizhelp.html', mode = HTML_RESIZE | HTML_POSITION, pos=None, size=None):
		"""Displays the given html file over the window"""
		if pos is not None:
			pos = str(pos[0]) + ' ' + str(pos[1])
		if size is not None:
			size = str(size[0]) + ' ' + str(size[1])
		setOption('viz.html.pos',pos)
		setOption('viz.html.size',size)
		_ipcSend(_VIZ_DISPLAYSET,14,mode,filename,0.0,0.0,0.0,0.0)
		setOption('viz.html.pos',None)
		setOption('viz.html.size',None)

	def hideHTML(self):
		"""Hides the html window"""
		_ipcSend(_VIZ_DISPLAYSET,15,0,'',0.0,0.0,0.0,0.0)

	def select(self,pos=None,mode=WINDOW_NORMALIZED):
		"""Returns the selected sub-window"""
		if pos is None:
			return VizWindow._GetObject(_ipcSend(_VIZ_DISPLAYGET,12,0,'',0.0,0.0,0.0,0.0))
		return VizWindow._GetObject(_ipcSend(_VIZ_DISPLAYGET,13,mode,'',pos[0],pos[1],0.0,0.0))

	def activate(self):
		"""Activates the graphics window by bringing it to the foreground"""
		_ipcSend(_VIZ_DISPLAYSET,16,0,'',0.0,0.0,0.0,0.0)

window = _WindowInterface()

def getFocusedNode():
	"""Returns the GUI object that currently has input focus"""
	return _GetNode(_ipcSend(_VIZ_CHILDGET,_FOCUSED_NODE,0,'',0.0,0.0,0.0,0.0))

def getModalNode():
	"""Returns the top most GUI modal node"""
	return _GetNode(_ipcSend(_VIZ_CHILDGET,_MODAL_NODE,0,'',0.0,0.0,0.0,0.0))

def quit():
	"""Close the graphical window"""
	_ipcSend(_VIZ_QUIT,0,0,'',0.0,0.0,0.0,0.0)

@DeprecateObject
def reset(what, layerNum = -99, viewpoint = _MAIN_VIEWPOINT):
	"""Reset the given attributes
	Can be a combination of viz.HEAD_POS, viz.HEAD_ORI, or viz.BODY_ORI"""
	_ipcSend(_VIZ_RESET,viewpoint,what,'',0.0,0.0,0.0,0.0)

def get(what, option = RELATIVE, viewpoint = _MAIN_VIEWPOINT):
	"""Get certain runtime attributes from Vizard.
	See documentation for more details"""
	if what == VELOCITY:
		return _ipcSend(_VIZ_GETVELOCITY,viewpoint,option,'',0.0,0.0,0.0,0.0)
	elif what == HEAD_LIGHT:
		return MainView.getHeadLight()
	elif what == MAIN_VIEWPOINT:
		return MainView
	elif what == MAIN_WINDOW:
		return MainWindow
	else:
		return _ipcSend(_VIZ_GET,what,viewpoint,'',0.0,0.0,0.0,0.0)

def getNodeList():
	"""Returns a list of all the nodes"""
	vals = _ipcSend(_VIZ_GET,_NODE_LIST,0,'',0.0,0.0,0.0,0.0)
	return [ _GetNode(id) for id in vals ]

def getSceneList():
	"""Returns a list of all the scenes"""
	vals = _ipcSend(_VIZ_GET,_SCENE_LIST,0,'',0.0,0.0,0.0,0.0)
	return [ VizScene._GetObject(id) for id in vals ]

def getViewList():
	"""Returns a list of all the views"""
	vals = _ipcSend(_VIZ_GET,_VIEW_LIST,0,'',0.0,0.0,0.0,0.0)
	return [ VizView._GetObject(id) for id in vals ]

def getWindowList(drawOrder=False):
	"""Returns a list of all the windows"""
	vals = _ipcSend(_VIZ_GET,_WINDOW_LIST,drawOrder,'',0.0,0.0,0.0,0.0)
	return [ VizWindow._GetObject(id) for id in vals ]

def getFrameNumber():
	"""Get the current frame number"""
	return _ipcSend(_VIZ_GET,FRAME_NUMBER,0,'',0.0,0.0,0.0,0.0)

def getFrameTime():
	"""Get start time of the current frame"""
	return _ipcSend(_VIZ_GET,FRAME_TIMESTAMP,0,'',0.0,0.0,0.0,0.0)

def getFrameElapsed():
	"""Get the elapsed time between the beginning of current frame and last frame"""
	return _ipcSend(_VIZ_GET,_FRAME_ELAPSED,0,'',0.0,0.0,0.0,0.0)

def tick():
	"""Get the current time tick"""
	return _ipcSend(_VIZ_GET,_TIME_TICK,0,'',0.0,0.0,0.0,0.0)

class ElapsedTimer(object):
	"""Class for retrieving elapsed time between successive calls to getElapsed()"""
	def __init__(self, timeFunc=getFrameTime):
		self._func = timeFunc
		self._time = timeFunc()

	def reset(self):
		"""Reset reference time to now"""
		self._time = self._func()

	def getReferenceTime(self):
		"""Get reference time for computing elapsed time"""
		return self._time

	def getElapsed(self):
		"""Get elapsed time since last call or reset"""
		now = self._func()
		elapsed = now - self._time
		self._time = now
		return elapsed

def splashScreen(textureName):
	_ipcSend(_VIZ_SPLASHSCREEN,0,0,textureName,0.0,0.0,0.0,0.0)

def director(function,*args,**kw):
	"""Execute a director function"""
	_ipcSendDirector(function, args, kw, None)

def directorPool(pool, function, *args, **kw):
	"""Execute a direction function in the specified pool"""
	_ipcSendDirector(function, args, kw, pool)

@DeprecateFunction('viz.setDirectorMode', '')
def setDirectorMode(mode):
	"""Set director function mode"""
	_ipcSend(_VIZ_DIRECTORMODE,mode,0,'',0.0,0.0,0.0,0.0)

def sendEvent(event,*args):
	"""Send a custom event"""
	return _ipcSendCustomEvent(event,args)

def postEvent(event,*args):
	"""Post a custom event"""
	_ipcSendPostEvent(event,args)

def postFunctionCall(func,*args,**kw):
	"""Post a function call to the main thread"""
	_ipcSendPostFunctionCall(func,args,kw)

def sendFunctionCall(func, *args, **kw):
	"""Send a function call to the main thread and wait for result"""
	return _ipcSendFunctionCall(func,args,kw)

def getEventID(eventName):
	"""Generates a unique event ID given a name"""
	return _ipcSend(_VIZ_GETEVENTID,0,0,eventName,0.0,0.0,0.0,0.0)

def getEventName(event):
	"""Returns name of the event with the given ID"""
	return _ipcSend(_VIZ_GETEVENTID,3,event,'',0.0,0.0,0.0,0.0)

def getNumHandlers(event):
	"""Returns the number of handlers registered for the event"""
	return _ipcSend(_VIZ_GETEVENTID,1,event,'',0.0,0.0,0.0,0.0)

def getCurrentEvent():
	"""Returns the currently triggered event"""
	return _ipcSend(_VIZ_GETEVENTID,2,0,'',0.0,0.0,0.0,0.0)

def setEventAction(flags):
	"""Set the action to take for the current event"""
	_ipcSend(_VIZ_GETEVENTID,4,flags,'',0.0,0.0,0.0,0.0)

def clearCache(mode = TEXTURE_CACHE | NODE_CACHE, name=''):
	"""Clear objects cached by Vizard"""
	_ipcSend(_VIZ_CLEARCACHE,mode,0,name,0.0,0.0,0.0,0.0)

def version():
	"""Return the version of vizard"""
	return getOption('viz.version')

def compareVersion(ver,current=None):
	"""Compares the specified version string with the current version
	Returns:	-1 if version is less than current
				1 if version is greater than current
				0 if versions are equal"""
	if current is None:
		current = version()
	return _ipcSendEx(8, (ver,current))

def requireVersion(ver,mode='<='):
	"""Makes sure the current version is compatible with the given version.
	If not, the program will exit"""
	c = compareVersion(ver)
	pop_message = ''
	if mode == '<=':
		if c > 0:
			pop_message = 'This script requires version %s or higher of Vizard'
	elif mode == '<':
		if c >= 0:
			pop_message = 'This script requires a version of Vizard higher than %s'
	elif mode == '=':
		if c != 0:
			pop_message = 'This script requires version %s of Vizard'
	elif mode == '>=':
		if c < 0:
			pop_message = 'This script requires version %s or lower of Vizard'
	elif mode == '>':
		if c <= 0:
			pop_message = 'This script requires a version of Vizard lower than %s'

	if pop_message:
		message(pop_message%(ver))
		quit()
		sys.exit()

def waitTime(seconds):
	"""Wait for the given amount of time to pass
	ONLY use in a director function"""
	_ipcSend(_VIZ_WAITTIME,0,0,'',seconds,0.0,0.0,0.0)

ENVMAP_FORMATS = [	 ('_posx','_negx','_posy','_negy','_posz','_negz')
					,('_right','_left','_up','_down','_front','_back')
					,('_r','_l','_u','_d','_f','_b')
					,('_rt','_lf','_up','_dn','_fr','_bk')
]

#************************************************************
def add(what,*args,**kw):
	"""Add an object to your world
	@return None"""
	if isinstance(what,int):
		if what == WINDOW:
			return addWindow(*args,**kw)
		elif what == VIEWPOINT:
			return addView(*args,**kw)
		elif what == SCENE:
			return addScene(*args,**kw)
		elif what == TEXT3D:
			return addText(*args,**kw)
		elif what == CHECKBOX:
			return addCheckbox(*args,**kw)
		elif what == SLIDER:
			return addSlider(*args,**kw)
		elif what == BUTTON:
			return addButton(*args,**kw)
		elif what == RADIO:
			return addRadioButton(*args,**kw)
		elif what == TEXTBOX:
			return addTextbox(*args,**kw)
		elif what == PROGRESS_BAR:
			return addProgressBar(*args,**kw)
		elif what == BUTTON_LABEL:
			return addButtonLabel(*args,**kw)
		elif what == DROPLIST:
			return addDropList(*args,**kw)
		elif what == TEXQUAD:
			return addTexQuad(*args,**kw)
		elif what == GROUP:
			return addGroup(*args,**kw)
		elif what == LIGHT:
			return addLight(*args,**kw)
		elif what == ANIMATION_PATH:
			return addAnimationPath(*args,**kw)
		elif what == CONTROL_POINT:
			return addControlPoint(*args,**kw)
		elif what == NETWORK:
			return addNetwork(*args,**kw)
		elif what == MAILBOX:
			return addMailbox(*args,**kw)
		elif what == ENVIRONMENT_MAP:
			return addEnvironmentMap(*args,**kw)
		else:
			raise ValueError('Unrecognized add type: '+str(what))


	else:

		fileType = _getFileExtension(what).upper()

		# VRMLs
		if fileType in _TypeModel:
			return addChild(what,*args,**kw)

		# Bitmaps
		elif fileType in _TypeImage:
			return addTexture(what,*args,**kw)

		# Audio
		elif fileType in _TypeAudio:
			return addAudio(what,*args,**kw)

		# Video
		elif fileType in _TypeVideo:
			return addVideo(what,*args,**kw)

		# Avatar
		elif fileType in _TypeAvatar:
			return addAvatar(what,*args,**kw)

		# Sensor plug-in
		elif fileType == 'DLS':
			return addSensor(what)

		# Renderer plug-in
		elif fileType == 'DLR':
			return addRenderer(what,*args,**kw)

		# Custom child plug-in
		elif fileType == 'DLC':
			return addCustomNode(what,*args,**kw)

		# Modifier plug-in
		elif fileType == 'DLM':
			return addModifier(what,*args,**kw)

		# Image Gen plug-in
		elif fileType == 'DLT':
			return addImageGen(what,*args,**kw)

		# Extension plug-in
		elif fileType == 'DLE':
			return addExtension(what,*args,**kw)

		# Viz Face File
		elif fileType in _TypeFace:
			return addFace(what,*args,**kw)

		else:
			raise ValueError('Unrecognized file extension: '+fileType)

def input(prompt, value=''):
	"""Get input from the user"""
	import vizinput
	retval = vizinput.input(prompt,value)
	try:
		num = int(retval)
		return num
	except ValueError:
		try:
			num = float(retval)
			return num
		except ValueError:
			return retval

def choose(prompt,choices, selection=0):
	"""Have the user choose from a list of options"""
	import vizinput
	return vizinput.choose(prompt,choices,selection)

def ask(prompt):
	"""Ask the user a yes or no question"""
	import vizinput
	return vizinput.ask(prompt)

def message(prompt):
	"""Display a message to the user"""
	import vizinput
	vizinput.message(prompt)

################################################################################################
################################################################################################
#											NETWORKING										   #
################################################################################################
################################################################################################

class NetworkEvent(Event):

	def __init__(self,data,port,address):
		Event.__init__(self)

		self.port = port
		self.address = address
		self.sender = data[0]
		self.data = self.__data = data[1]
		self.__props = data[2]
		self.__dict__.update(data[2])

	def getData(self): return self.__data
	def getProperties(self): return self.__props

	def __getitem__(self,i):
		if i == 0: #Sender
			return self.sender
		elif i == 1: #Typetags
			return ''
		elif i > 1: #Beginning of data
			return self.data[i-2]
		else: #Negative index
			return self.data[i]

class RawNetworkEvent(Event):

	def __init__(self,data,port,address):
		Event.__init__(self)

		self.port = port
		self.address = address
		self.raw_data = data

# Header for all pickled network packets
_NETWORK_PICKLE_HEADER = b'PICKLED_PACKET:'
_NETWORK_PICKLE_HEADER_SIZE = len(_NETWORK_PICKLE_HEADER)

def _encodeNetworkPacket(args, kw):
	b = io.BytesIO()
	b.write(_NETWORK_PICKLE_HEADER)
	pickle.dump( (VizNetwork._getComputeName(), args, kw), b, protocol=pickle.HIGHEST_PROTOCOL )
	return b.getbuffer()

def _decodeNetworkPacket(buf, port, address):
	v = memoryview(buf)
	if v[:_NETWORK_PICKLE_HEADER_SIZE] == _NETWORK_PICKLE_HEADER:
		return NetworkEvent(pickle.loads(v[_NETWORK_PICKLE_HEADER_SIZE:]), port, address)
	else:
		return RawNetworkEvent(bytes(buf), port, address)

class _NetworkInterface(object):
	"""For internal use only"""
	def getName(self):
		"""Return the name of this computer"""
		return _ipcSend(_VIZ_GET,_COMPUTER_NAME,0,'',0.0,0.0,0.0,0.0)

	def getIP(self):
		"""Return the IP address of this computer"""
		return _ipcSend(_VIZ_GET,_COMPUTER_IP,0,'',0.0,0.0,0.0,0.0)

	def addPort(self,port):
		"""Add a port to listen for network data"""
		_ipcSend(_VIZ_LISTENPORT,port,1,'',0.0,0.0,0.0,0.0)

	def removePort(self,port):
		"""Ignore network data from the following port"""
		_ipcSend(_VIZ_LISTENPORT,port,0,'',0.0,0.0,0.0,0.0)

	def broadcast(self, port, *args, **kw):
		"""Broadcast data on the specified port"""
		_ipcSend(_VIZ_SENDNETWORK,port,2,_encodeNetworkPacket(args,kw),0.0,0.0,0.0,0.0)

	def broadcastRaw(self, port, data):
		"""Broadcast raw bytes on the specified port"""
		_ipcSend(_VIZ_SENDNETWORK,port,2,data,0.0,0.0,0.0,0.0)

net = _NetworkInterface()

class VizNetwork(VizObject):

	_VizObjectCache = {}
	_VizObjectType = _VIZ_OBJECT_NETWORK

	_computerName = None

	@staticmethod
	def _getComputeName():
		if VizNetwork._computerName is None:
			VizNetwork._computerName = net.getName()
		return VizNetwork._computerName

	"""VizNetwork object"""
	def __init__(self, id, port=None):
		VizObject.__init__(self, id)
		if self.valid():
			if port is not None:
				self.port(port)

	def remove(self):
		"""Delete the network object"""
		_ipcSend(_VIZ_DELNETWORK,self.id,0,'',0.0,0.0,0.0,0.0)

	def send(self,*args,**kw):
		"""Send data to the network object"""
		_ipcSend(_VIZ_SENDNETWORK,self.id,1,_encodeNetworkPacket(args,kw),0.0,0.0,0.0,0.0)

	def sendRaw(self,data):
		"""Send raw bytes to the network object"""
		_ipcSend(_VIZ_SENDNETWORK,self.id,1,data,0.0,0.0,0.0,0.0)

	def port(self,val):
		"""Set the port to communicate over"""
		_ipcSend(_VIZ_NETWORKSET,self.id,1,'',val,0.0,0.0,0.0)

	def getPort(self):
		"""Get the port to communicate over"""
		return _ipcSend(_VIZ_NETWORKGET,self.id,1,'',0.0,0.0,0.0,0.0)

	def setAddress(self, address, broadcast=False):
		"""Set the address to send messages to"""
		return _ipcSend(_VIZ_NETWORKSET,self.id,2,address,broadcast,0.0,0.0,0.0)

	def getAddress(self):
		"""Get the address messages will be sent to"""
		return _ipcSend(_VIZ_NETWORKGET,self.id,2,'',0.0,0.0,0.0,0.0)

	def setBindAddress(self, address):
		"""Set the local bind address for sending messages"""
		return _ipcSend(_VIZ_NETWORKSET,self.id,3,address,0.0,0.0,0.0,0.0)

	def getBindAddress(self):
		"""Get the local bind address for sending messages"""
		return _ipcSend(_VIZ_NETWORKGET,self.id,3,'',0.0,0.0,0.0,0.0)

def addNetwork(address,broadcast=False,**kw):
	"""Add a network object"""
	return VizNetwork(_ipcSend(_VIZ_ADDNETWORK,broadcast,0,address,0.0,0.0,0.0,0.0),**kw)

NO_ROTATE		= 0
PIVOT_ROTATE	= 1
BLEND_ROTATE	= 2

###################################
######## Action Controller ########
###################################

class ActionController(EventClass):

	class ActionPool(object):
		def __init__(self,id):
			self.id = id
			self.actionList = []
			self.idleList = []
			self.curAction = None
			self.callAction = None
			self.paused = False

		def pause(self,state):
			self.paused = state
			if self.curAction:
				self.callAction.pause(state)

		def end(self):
			if self.curAction:
				try:
					self.callAction.end(self.curAction._obj_)
				except:
					HandleException()
				ActionClass.end(self.curAction,self.curAction._obj_)

	DummyPool = ActionPool(0)

	@staticmethod
	def __endErrorAction__(action):
		try:
			action.end(action._obj_)
		except:
			HandleException()
		ActionClass.end(action,action._obj_)

	@staticmethod
	def __beginAction__(object,action,pool,overtime=0):
		#Create new action
		newAction = action.actionclass(action,object)
		newAction._pool_ = pool

		#Begin the action
		try:
			newAction.begin(newAction._obj_)
		except:
			HandleException()
			ActionController.__endErrorAction__(newAction)
		else:
			if object._action:
				object._action.notifyBeginAction(newAction)

		#Update action with overtime
		if not newAction.finished() and overtime > 0:
			try:
				newAction.update(overtime,newAction._obj_)
			except:
				HandleException()
				ActionController.__endErrorAction__(newAction)

		return newAction

	@staticmethod
	def __updateAction__(action,elapsed):
		try:
			action.update(elapsed,action._obj_)
		except:
			HandleException()
			ActionController.__endErrorAction__(action)

	@staticmethod
	def __endAction__(object,action):
		#Action ended, notify callback
		if object._action:
			object._action.notifyEndAction(action)

	def __init__(self,node):
		EventClass.__init__(self)

		self.timerRunning = False
		self.node = node

		if isinstance(node,Removable):
			node.addRemoveCallback(self.remove)

		self.speed = 1.0
		self.allPaused = False

		self.actionPool = {}

		self.noActionCB = None
		self.beginActionCB = None
		self.endActionCB = None

		self.inCallback = False

		self.idlepose = -1

	def remove(self):
		self.unregister()
		self.endAction(ALL_POOLS)
		self.actionPool.clear()

	################
	#Public Methods#
	################

	def setCallback(self,event,func):
		if event == ACTION_END_EVENT:
			self.endActionCB = func
		elif event == ACTION_BEGIN_EVENT:
			self.beginActionCB = func
		elif event == ACTION_EMPTY_EVENT:
			self.noActionCB = func
		else:
			raise ValueError('Invalid callback event')

	def pauseActions(self, state, thread=0):

		if thread == ALL_POOLS:
			self.allPaused = state
			#Iterate over all actions in action map
			for pool in self.actionPool.values():
				pool.pause(state)
			return

		#Set the pause flag for the pool
		self.actionPool.get(thread,self.DummyPool).pause(state)

	def endAction(self, thread=0):

		if thread == ALL_POOLS:
			#Iterate over all pools in pool map
			for pool in self.actionPool.values():
				#Manually end the pool
				pool.end()
			return

		#End the action in the pool
		self.actionPool.get(thread,self.DummyPool).end()

	def startAction(self, thread=0):

		if thread == ALL_POOLS:
			#Iterate over all pools in pool map
			for pool in self.actionPool.values():
				#Start next action in pool
				self.__checkPool(pool)
			return

		#Make sure thread exists
		if thread in self.actionPool:
			#End the action in the pool
			self.__checkPool(self.actionPool[thread])

	def getAction(self, thread=0):

		#Make sure thread exists
		if not thread in self.actionPool:
			return None

		#Check if an action is running
		if self.actionPool[thread].curAction:
			#Return the action data
			return self.actionPool[thread].curAction._actiondata_
		return None

	def getActionInstance(self, thread=0):

		#Make sure thread exists
		if not thread in self.actionPool:
			return None

		#Check if an action is running
		return self.actionPool[thread].curAction

	def clearActionList(self, thread=0):

		if thread == ALL_POOLS:
			#Iterate over all actions in action list
			for actions in self.actionPool.values():
				#Delete all actions in list
				del actions.actionList[:]
			return

		#Delete the action list
		del self.actionPool.get(thread,self.DummyPool).actionList[:]

	def clearIdleList(self, thread=0):

		if thread == ALL_POOLS:
			#Iterate over all actions in idle list
			for actions in self.actionPool.values():
				#Delete all actions in list
				del actions.idleList[:]
			return

		#Delete the idle list
		del self.actionPool.get(thread,self.DummyPool).idleList[:]

	def clearPool(self, thread=0):

		if thread == ALL_POOLS:
			#Iterate over all actions in idle list
			for pool in self.actionPool.values():
				#Delete all actions in list
				del pool.idleList[:]
				del pool.actionList[:]
				pool.end()
			return

		#Make sure thread exists
		pool = self.actionPool.get(thread,self.DummyPool)
		del pool.idleList[:]
		del pool.actionList[:]
		pool.end()

	def runAction(self, action, thread=0):
		#Make sure pool exists
		self.__createthread(thread)
		pool = self.actionPool[thread]

		#Clear current actions from pool
		del pool.actionList[:]
		pool.end()

		#Add the action and current cluster mask to the end of the action list
		pool.actionList.append((action,get(CLUSTER_MASK)))

		#Make sure action starts now
		self.__checkPool(pool)

	def addAction(self, action, thread=0):
		#Create the thread in case it doesn't exist
		self.__createthread(thread)
		#Add the action and current cluster mask to the end of the action list
		self.actionPool[thread].actionList.append((action,get(CLUSTER_MASK)))

	def addIdle(self, action, thread=0):
		#Create the thread in case it doesn't exist
		self.__createthread(thread)
		#Add the action and current cluster mask to the end of the idle list
		self.actionPool[thread].idleList.append((action,get(CLUSTER_MASK)))

	#################
	#Private Methods#
	#################

	def __createthread(self,num):

		#Check if thread already exists
		if num in self.actionPool:
			return

		#Initialize the action list and current action
		self.actionPool[num] = ActionController.ActionPool(num)
		self.actionPool[num].pause(self.allPaused)

		#Make sure a timer is running
		if not self.timerRunning:
			self.timerRunning = True
			self.callback(UPDATE_EVENT,self.__update,priority=PRIORITY_TIMERS-1) #Update right before timers

	def __destroythread(self,num):

		#Delete the action pool
		self.actionPool.pop(num,None)

		#If no threads exist then kill the timer
		if not self.actionPool:
			self.timerRunning = False
			self.callback(UPDATE_EVENT,0)

	def __update(self,e):

		#Check global pause flag
		if _vizPaused:
			return

		#Calculate elapsed time
		elaps = e.elapsed * self.speed

		#Need to iterate over copy because dictionary can change during iteration
		for pool in list(self.actionPool.values()):

			#Don't update paused pools
			if pool.paused:
				continue

			#Get the current action
			curAction = pool.curAction

			if curAction:

				#Update the action
				if not curAction._completed_:
					try:
						pool.callAction.update(elaps,curAction._obj_)
					except:
						HandleException()
						pool.end()

				#Check if pool is finished
				if curAction._completed_:
					#Store overtime of action
					overtime = curAction._overtime_
					#Notify that the action has ended
					self.notifyEndAction(curAction)
					#Set current action to NULL
					pool.curAction = None
					pool.callAction = None
					#Move on to next action
					if not self.nextAction(pool,overtime):
						#No more actions in this thread, notify callback
						self.notifyNoActions(pool.id)

			else:
				#Move on to next action
				self.nextAction(pool)

	def __checkPool(self, pool):

		#Prevent recursion from callbacks readding actions
		if self.inCallback or pool.paused:
			return

		#Get current action
		curAction = pool.curAction

		#Check if action has finished
		if curAction and curAction.finished():
			#Store overtime of action
			overtime = curAction._overtime_
			#Notify that the action has ended
			self.notifyEndAction(curAction)
			#Set current action to NULL
			pool.curAction = None
			pool.callAction = None
			#Move on to next action
			if not self.nextAction(pool,overtime):
				#No more actions in this thread, notify callback
				self.notifyNoActions(pool.id)
		elif not curAction:
			#Start action on empty pool
			self.nextAction(pool)

	def nextAction(self, pool, overtime=0):
		action = None
		if pool.actionList:
			#Get the next action and begin it
			action = pool.actionList.pop(0)
		elif pool.idleList:
			#Randomly select an action from the idle list
			action = random.choice(pool.idleList)

		if action:
			#Create the action and save its cluster mask and pool number
			newAction = action[0].actionclass(action[0],self.node)
			newAction._pool_ = pool.id

			#Save the new action in the current pool
			pool.curAction = newAction

			#Save cluster masked version of action if clustering enabled
			if _clustered:
				callAction = MaskedObject(newAction,action[1])
			else:
				callAction = newAction
			pool.callAction = callAction

			#Begin the action
			try:
				callAction.begin(newAction._obj_)
			except:
				HandleException()
				pool.end()
			else:
				self.notifyBeginAction(newAction)

			#Update action with overtime
			if not callAction.finished() and overtime > 0:
				try:
					callAction.update(overtime,newAction._obj_)
				except:
					HandleException()
					pool.end()
			return True

		#No action in this pool, destroy it
		self.__destroythread(pool.id)

		#For avatars
		if pool.id == 0 and self.idlepose > -1:
			self.node.state(self.idlepose)

		return False

	def notifyNoActions(self,thread):
		#Create event object
		e = Event()
		e.object = self.node
		e.pool = thread

		#Pass event to handlers
		if self.noActionCB:
			self.noActionCB(e)
		else:
			sendEvent(ACTION_EMPTY_EVENT,e)

	def notifyBeginAction(self,action):
		#Create event object
		e = Event()
		e.object = self.node
		e.action = action._actiondata_
		e.pool = action._pool_
		e.instance = action

		#Pass event to handlers
		self.inCallback = True
		try:
			if self.beginActionCB:
				self.beginActionCB(e)
			else:
				sendEvent(ACTION_BEGIN_EVENT,e)
		finally:
			self.inCallback = False

	def notifyEndAction(self,action):
		#Create event object
		e = Event()
		e.object = self.node
		e.action = action._actiondata_
		e.pool = action._pool_
		e.instance = action

		#Pass event to handlers
		self.inCallback = True
		try:
			if self.endActionCB:
				self.endActionCB(e)
			else:
				sendEvent(ACTION_END_EVENT,e)
		finally:
			self.inCallback = False

################################
######## Action Classes ########
################################

class ActionData(object):
	def __init__(self):
		self.actionclass = None
		self.object = None

class ActionClass(object):

	def __init__(self,action,obj):
		self._actiondata_ = action
		self._completed_ = False
		self._paused_ = False
		self._pool_ = None
		self._overtime_ = 0
		self._actor_ = obj
		if action.object is not None:
			self._obj_ = action.object
		else:
			self._obj_ = obj

	def begin(self,obj):
		#Virtual method
		pass

	def update(self,elapsed,obj):
		#Virtual method
		pass

	def end(self,obj):
		self._completed_ = True

	def complete(self):
		if hasattr(self,'elapsed') and hasattr(self,'duration'):
			self._overtime_ = self.elapsed - self.duration
		self.end(self._obj_)

	def finished(self):
		return self._completed_

	def pause(self,state):
		self._paused_ = state

	def paused(self):
		return self._paused_

	def getAction(self):
		return self._actiondata_

	def getObject(self):
		return self._obj_

	def getTime(self):
		return getattr(self,'elapsed',-1.0)

	def getDuration(self):
		return getattr(self,'duration',-1.0)

#Backwards compatibility
VizTheme = DeprecateObject(Theme)
VizIntersect = DeprecateObject(Intersect)
KEYBOARD_EVENT = DeprecateObject(KEYDOWN_EVENT)
MOUSEBUTTON_EVENT = DeprecateObject(MOUSEDOWN_EVENT)
SCROLL_EVENT = DeprecateObject(MOUSEWHEEL_EVENT)
CRYSTAL = DeprecateObject(STEREO_VERT)
STACK = DeprecateObject(STEREO_VERT)
STEREO = DeprecateObject(STEREO_HORZ)
INTERLACE = DeprecateObject(INTERLACE_VERT)
MODULATE = DeprecateObject(TEXMODULATE)
DECAL = DeprecateObject(TEXDECAL)
BLEND_TEX = DeprecateObject(TEXBLEND)
ABSOLUTE_LOCAL = DeprecateObject(ABS_PARENT)
RELATIVE_WORLD = DeprecateObject(REL_PARENT)
RELATIVE_LOCAL = DeprecateObject(REL_LOCAL)
ABSOLUTE_WORLD = DeprecateObject(ABS_GLOBAL)
COLLISION = DeprecateObject(INTERSECTION)

#Special files in windows system path that will be included with published EXE
_PublishSystemFiles = set(['pythoncom27.dll','pywintypes27.dll'])

#DLLs to exclude from published EXE
_PublishExcludeDLL = set(['crashrpt1401.dll'])

def _GetDependencies(resources,dlls):
	"""For internal use only"""

	# Import modules that should always be included
	import vizinput # Needed for popup messages
	import unicodedata # Needed for various encodings

	resourceDepend = set() #Set of resource dependencies
	dllDepend = set() #Set of dll dependencies
	pyDepend = set() #Set of python module dependencies

	winPath = os.path.abspath(os.environ['WINDIR']).lower() #Get windows path
	vizardBinPath = os.path.abspath(os.path.join(res.getVizardPath(),'bin')) #Get Vizard bin path
	vizardPath = os.path.abspath(res.getVizardPath()).lower() # Get root Vizard path
	scriptPath = os.path.abspath(sys.modules['__main__'].__file__)
	scriptDir = os.path.join(os.path.dirname(scriptPath), '').lower()
	importedModules = list(sys.modules.values())

	if not winPath.endswith('\\'): #Make sure path ends with slash
		winPath += '\\'

	def _AbsPath(file):
		return os.path.abspath(file)

	def _IsExternalPath(path):
		p = path.lower()
		return not p.startswith(vizardPath) and not p.startswith(scriptDir)

	def _GetModulePath(m):

		# Check for cached file attribute (pyc)
		if hasattr(m, '__cached__'):
			if m.__cached__:
				file = _AbsPath(m.__cached__)
				if os.path.isfile(file):
					return file

		# Check for source file attribute (py)
		if hasattr(m, '__file__'):
			if m.__file__:
				return _AbsPath(m.__file__)

		return ''

	def _AddModule(name,pySet):
		for path in sys.path:
			module_path = os.path.join(path,name)
			if os.path.isfile(module_path):
				pySet.add(_AbsPath(module_path))
				return

	def _CheckForHTMLViewer(pySet,dllSet,resourceSet):
		for file in dllSet.union(resourceSet):
			file = os.path.basename(file).lower()
			if file == 'vizhtmlviewer.exe':
				dllDepend.add(os.path.join(vizardBinPath,'crashrpt1401.dll'))
				dllDepend.add(os.path.join(vizardBinPath,'mfc90u.dll'))
				dllDepend.add(os.path.join(vizardBinPath,'Microsoft.VC90.MFC.manifest'))
				return

	pyWinTypesDll = f'pywintypes{sys.version_info.major}{sys.version_info.minor}.dll'
	pythonComDll = f'pythoncom{sys.version_info.major}{sys.version_info.minor}.dll'
	def _CheckForWin32COM(pySet,dllSet,resourceSet):
		pyAndDLL = pySet.union(dllSet)
		for file in pyAndDLL:
			file = os.path.basename(file).lower()
			if file == pyWinTypesDll:
				_AddModule('pywintypes.py',pySet)
			elif file == pythonComDll:
				_AddModule('pythoncom.py',pySet)

	def _CheckForOculusRuntime(pySet, dllSet, resourceSet):
		import fnmatch
		oculus_runtime_files = []
		for path in dllSet:
			if fnmatch.fnmatch(os.path.basename(path), 'libovr*.dll'):
				if _IsExternalPath(path):
					oculus_runtime_files.append(path)
		for path in oculus_runtime_files:
			dllSet.discard(path)

	def _IsSystemFile(file):
		fileLower = file.lower()
		return os.path.commonprefix([winPath,fileLower]) == winPath and os.path.basename(fileLower) not in _PublishSystemFiles

	def _IsExcludeDLL(file):
		name = os.path.basename(file).lower()
		return name in _PublishExcludeDLL

	# Generate dictionary of module path prefixes to associated zip archives
	import zipimport
	zip_libs = {}

	# Python lib
	try:
		fullpath = os.path.join(vizardBinPath, 'compiler', 'pythonlib.zip')
		ziplib = zipimport.zipimporter(fullpath)
		zip_libs[os.path.join(vizardBinPath, 'lib').lower()] = ziplib
	except:
		pass

	# Vizard lib
	try:
		fullpath = os.path.join(vizardBinPath, 'compiler', 'vizlib.zip')
		ziplib = zipimport.zipimporter(fullpath)
		zip_libs[os.path.join(vizardPath, 'python').lower()] = ziplib
	except:
		pass

	def _IsZipModule(filename, module):
		if filename.endswith(('.py','.pyc')):
			module_name = module.__name__
			if module_name == '_frozen_importlib_external':
				return True
			module_name_path = ''
			if '.' in module_name:
				module_name_path = module_name.replace('.', os.path.sep)
			file_lower = filename.lower()
			for zip_prefix, zip_archive in zip_libs.items():
				if file_lower.startswith(zip_prefix):
					if zip_archive.find_spec(module_name) is not None:
						return True
					if module_name_path and zip_archive.find_spec(module_name_path) is not None:
						return True
		return False

	# Iterate through all DLLs
	for d in dlls:
		file = _AbsPath(d)
		#Don't add DLLs in Windows path
		if not _IsSystemFile(file) and not _IsExcludeDLL(file):
			dllDepend.add(file)

	# Iterate through all resources
	for r in resources:
		file = _AbsPath(r)
		if file not in dllDepend:
			#Save resource only if it does not reside in windows path
			if not _IsSystemFile(file):
				resourceDepend.add(file)

	# Iterate through loaded modules
	for m in importedModules:

		# Python creates None module entries to cache failed loads, so check for None
		if m is not None:

			# Get module file path
			file = _GetModulePath(m)

			# Check if module is part of zip archive
			if _IsZipModule(file, m):
				continue

			# Make sure module isn't already part of DLL set
			if file and file not in dllDepend:
				pyDepend.add(file)

	#Add runtime library files
#	dllDepend.add(os.path.join(vizardBinPath,'msvcp90.dll'))
#	dllDepend.add(os.path.join(vizardBinPath,'msvcr90.dll'))
#	dllDepend.add(os.path.join(vizardBinPath,'Microsoft.VC90.CRT.manifest'))

	#Check for html viewer files
	_CheckForHTMLViewer(pyDepend,dllDepend,resourceDepend)

	#Check for win32com files
	_CheckForWin32COM(pyDepend,dllDepend,resourceDepend)

	#Check for Oculus runtime files
	_CheckForOculusRuntime(pyDepend,dllDepend,resourceDepend)

	#Code taken from import site to get all 'pth' files that are used to modify sys path
	prefixes = [sys.prefix]
	if sys.exec_prefix != sys.prefix:
		prefixes.append(sys.exec_prefix)
	for prefix in prefixes:
		sitedirs = [prefix, os.path.join(prefix, "lib", "site-packages")]
		for sitedir in sitedirs:
			try:
				names = os.listdir(sitedir)
			except os.error:
				continue
			for name in names:
				if name.endswith(os.extsep + "pth"):
					pyDepend.add(os.path.join(sitedir, name))

	#Apply filters to all files
	if _publishFilters:

		def _passesFilter(filename):
			for filterFunc in _publishFilters:
				if filterFunc(filename):
					return False
			return True


		def _filterSet(s):
			return [ f for f in s if _passesFilter(f) ]

		return _filterSet(dllDepend),_filterSet(resourceDepend),_filterSet(pyDepend)

	return list(dllDepend),list(resourceDepend),list(pyDepend)
