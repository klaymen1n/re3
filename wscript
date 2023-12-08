#! /usr/bin/env python
# encoding: utf-8
# klaymen1n

from __future__ import print_function
from waflib import Logs, Context, Configure
import os
import sys

VERSION = '1.0'
APPNAME = 're:vc'
top = '.'

Context.Context.line_just = 55

projects=['vendor/librw', 'src']

@Configure.conf
def check_pkg(conf, package, uselib_store, fragment, *k, **kw):
	errormsg = '{0} not available! Install {0} development package. Also you may need to set PKG_CONFIG_PATH environment variable'.format(package)
	confmsg = 'Checking for \'{0}\' sanity'.format(package)
	errormsg2 = '{0} isn\'t installed correctly. Make sure you installed proper development package for target architecture'.format(package)

	try:
		conf.check_cfg(package=package, args='--cflags --libs', uselib_store=uselib_store, *k, **kw )
	except conf.errors.ConfigurationError:
		conf.fatal(errormsg)

	try:
		conf.check_cxx(fragment=fragment, use=uselib_store, msg=confmsg, *k, **kw)
	except conf.errors.ConfigurationError:
		conf.fatal(errormsg2)

@Configure.conf
def get_taskgen_count(self):
	try: idx = self.tg_idx_count
	except: idx = 0 # don't set tg_idx_count to not increase counter
	return idx


def options(opt):
	grp = opt.add_option_group('Common options')
	
	grp.add_option('--disable-warns', action = 'store_true', dest = 'DISABLE_WARNS', default = False,
		help = 'disable warinigs while building [default: %default]')

	grp.add_option('-4', '--32bits', action = 'store_true', dest = 'TARGET32', default = False,
		help = 'allow targetting 32-bit engine(Linux/Windows/OSX x86 only) [default: %default]')

	grp.add_option('-D', '--debug-engine', action = 'store_true', dest = 'DEBUG_ENGINE', default = False,
		help = 'build with -DDEBUG [default: %default]')
	
	opt.load('subproject compiler_optimizations')

	opt.add_subproject(projects)

	opt.load('xcompile compiler_cxx compiler_c sdl2 clang_compilation_database strip_on_install waf_unit_test subproject')
	if sys.platform == 'win32':
		opt.load('msvc msdev msvs')
	opt.load('reconfigure')

def check_deps(conf):

	if conf.env.DEST_OS != 'android':
		if conf.env.DEST_OS != 'win32':
			conf.check_cfg(package='sdl2', uselib_store='SDL2', args=['--cflags', '--libs'])
			conf.check_cfg(package='openal', uselib_store='OPENAL', args=['--cflags', '--libs'])
			conf.check_cfg(package='libmpg123', uselib_store='MPG123', args=['--cflags', '--libs'])
			conf.check_cfg(package='sndfile', uselib_store='SNDFILE', args=['--cflags', '--libs'])
			conf.check_cfg(package='gl', uselib_store='GL', args=['--cflags', '--libs'])
			conf.check_cfg(package='x11', uselib_store='X11', args=['--cflags', '--libs'])
			conf.check_cfg(package='glfw3', uselib_store='GLFW', args=['--cflags', '--libs'])


def configure(conf):
	conf.load('fwgslib reconfigure compiler_optimizations')

	# Force XP compability, all build targets should add
	# subsystem=bld.env.MSVC_SUBSYSTEM
	# TODO: wrapper around bld.stlib, bld.shlib and so on?
	conf.env.MSVC_SUBSYSTEM = 'WINDOWS,5.01'
	conf.env.MSVC_TARGETS = ['x64'] # explicitly request x86 target for MSVC
	if conf.options.TARGET32:
		conf.env.MSVC_TARGETS = ['x86']

	if sys.platform == 'win32':
		conf.load('msvc_pdb_ext msdev msvs msvcdeps')
	conf.load('subproject xcompile compiler_c compiler_cxx gccdeps gitversion clang_compilation_database waf_unit_test enforce_pic')

	conf.env.BIT32_MANDATORY = conf.options.TARGET32
	if conf.env.BIT32_MANDATORY:
		Logs.info('WARNING: will build engine for 32-bit target')
		conf.load('force_32bit')

	if conf.options.DEBUG_ENGINE:
		conf.env.append_unique('DEFINES', [
			'DEBUG'
		])

	if conf.options.DISABLE_WARNS:
		compiler_optional_flags = ['-w']
	else:
		compiler_optional_flags = [
			'-Wall',
			'-fdiagnostics-color=always',
			'-Wcast-align',
			'-Wuninitialized',
			'-Winit-self',
			'-Wstrict-aliasing',
			'-Wno-reorder',
			'-Wno-unknown-pragmas',
			'-Wno-unused-function',
			'-Wno-unused-but-set-variable',
			'-Wno-unused-value',
			'-Wno-unused-variable',
			'-faligned-new',
		]

	c_compiler_optional_flags = [
		'-fnonconst-initializers' # owcc
	]

	cflags, linkflags = conf.get_optimization_flags()


	flags = []
	
	if conf.env.DEST_OS != 'win32':
		flags += ['-pipe', '-fPIC', '-L'+os.path.abspath('.') + 'build/vendor']
	if conf.env.COMPILER_CC != 'msvc':
		flags += ['-pthread']
	flags += ['-funwind-tables', '-g']
	
	if conf.env.DEST_OS != 'win32':
		cflags += flags
		linkflags += flags

	cxxflags = list(cflags)
	if conf.env.DEST_OS != 'win32':
		cxxflags += ['-std=c++11','-fpermissive']

	if conf.env.COMPILER_CC == 'gcc':
		conf.define('COMPILER_GCC', 1)

	if conf.env.COMPILER_CC != 'msvc':
		conf.check_cc(cflags=cflags, linkflags=linkflags, msg='Checking for required C flags')
		conf.check_cxx(cxxflags=cxxflags, linkflags=linkflags, msg='Checking for required C++ flags')

		conf.env.append_unique('CFLAGS', cflags)
		conf.env.append_unique('CXXFLAGS', cxxflags)
		conf.env.append_unique('LINKFLAGS', linkflags)

		cxxflags += conf.filter_cxxflags(compiler_optional_flags, cflags)
		cflags += conf.filter_cflags(compiler_optional_flags + c_compiler_optional_flags, cflags)

	conf.env.append_unique('CFLAGS', cflags)
	conf.env.append_unique('CXXFLAGS', cxxflags)
	conf.env.append_unique('LINKFLAGS', linkflags)
	conf.env.append_unique('INCLUDES', [os.path.abspath('common/')])

	check_deps( conf )
	conf.add_subproject(projects)
def build(bld):
	bld.add_subproject(projects)