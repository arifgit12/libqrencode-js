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
jsPipe = subprocess.Popen(emscriptenPath + ' -s INVOKE_RUN=0 libqrencode-js.bc', 
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

def applyTmpl(varName):
    return tmpl.replace('{{genCode}}', jsCode)\
               .replace('{{varName}}', varName)

os.chdir('../release/')

jsFileName = 'libqrencode-' + ver + '.js'
showState('making ' + jsFileName)
jsFile = open(jsFileName,'w')
jsFile.write(applyTmpl('var qrencode'))
jsFile.close()
print 'ok'

jsMinFileName = 'libqrencode-' + ver + '.min.js'
showState('making ' + jsMinFileName)
r = subprocess.call('uglifyjs %s > %s' % (jsFileName, jsMinFileName),
    shell=True)
assert r == 0, buildFailed
print 'ok'

jqFileName = 'jquery.libqrencode-' + ver + '.js'
showState('making ' + jqFileName)
jqFile = open(jqFileName,'w')
jqFile.write(applyTmpl('jQuery.qrencode'))
jqFile.close()
print 'ok'

jqMinFileName = 'jquery.libqrencode-' + ver + '.min.js'
showState('making ' + jqMinFileName)
r = subprocess.call('uglifyjs %s > %s' % (jqFileName, jqMinFileName),
    shell=True)
assert r == 0, buildFailed
print 'ok'

print
