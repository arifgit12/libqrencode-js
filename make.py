#!/usr/bin/python

import os
import sys
import subprocess

JS_VER = 1

exec(open(os.path.expanduser('~/.emscripten'), 'r').read())
toolPath = os.path.join(EMSCRIPTEN_ROOT, 'tools')
emmakenPath = os.path.join(toolPath, 'emmaken.py')
emscriptenPath = os.path.join(EMSCRIPTEN_ROOT, 'emscripten.py')

buildFailed = 'Build failed'

if not os.path.exists('build'):
    os.makedirs('build')
os.chdir('build')

def showState(s):
    print
    print '================ ' + s
    print

showState('compiling libqrencode')
r = subprocess.call(emmakenPath + ' -D HAVE_CONFIG_H ../*.c', shell=True)
assert r == 0, buildFailed
print 'ok'

showState('linking libqrencode')
r = subprocess.call('llvm-link *.o -o libqrencode-js.bc', shell=True)
assert r == 0, buildFailed
print 'ok'

showState('compiling to JavaScript')
jsPipe = subprocess.Popen(emscriptenPath + ' -s INVOKE_RUN=0 -s OPTIMIZE=1 -s RELOOP=1 -s FAST_MEMORY=1 libqrencode-js.bc', 
    shell=True, stdout=subprocess.PIPE).stdout
print 'ok'

def readAll(h):
    r = ''
    while True:
        n = h.read()
        if n == '':
            break
        r = r + n
    return r

jsCode = readAll(jsPipe)

def loadVersion():
    f = open('../libqrencode/configure.ac')
    major = 0
    majorStr = 'MAJOR_VERSION='
    minor = 0
    minorStr = 'MINOR_VERSION='
    micro = 0
    microStr = 'MICRO_VERSION='
    for l in f.readlines():
        if l.startswith(majorStr):
            major = int(l[len(majorStr):])
        if l.startswith(minorStr):
            minor = int(l[len(minorStr):])
        if l.startswith(microStr):
            micro = int(l[len(microStr):])
            
    return '%s.%s.%s_%s' % (major, minor, micro, JS_VER)

ver = loadVersion()

tmplVars = {'genCode': jsCode}

tmpl = readAll(open('../libqrencode.tmpl.js'))

def jsApplyTmpl(varName):
    return tmpl.replace('{{genCode}}', jsCode)\
               .replace('{{varName}}', varName)

os.chdir('../release/')

jsFileName = 'libqrencode-' + ver + '.js'
showState('making ' + jsFileName)
jsFile = open(jsFileName,'w')
jsFile.write(jsApplyTmpl('var qrencode'))
jsFile.close()
print 'ok'

jsMinFileName = 'libqrencode-' + ver + '.min.js'
showState('making ' + jsMinFileName)
r = subprocess.call('uglifyjs %s > %s' % (jsFileName, jsMinFileName),
    shell=True)
assert r == 0, buildFailed
print 'ok'

exampleHtml = "example.html"
showState('making ' + exampleHtml)
exampleHtmlText = readAll(open('../example.tmpl.html'))
open(exampleHtml,"w").write(exampleHtmlText.replace(
    '{{libqrencode.js}}',jsMinFileName))
print 'ok'

showState('making symlinks')
jsLinkName = 'libqrencode-latest.js'
jsMinLinkName = 'libqrencode-latest.min.js'
os.chdir('../test/')
if os.path.exists(jsLinkName):
    os.remove(jsLinkName)
if os.path.exists(jsMinLinkName):
    os.remove(jsMinLinkName)
os.symlink('../release/' + jsFileName, jsLinkName)
os.symlink('../release/' + jsMinFileName, jsMinLinkName)
print 'ok'

print

